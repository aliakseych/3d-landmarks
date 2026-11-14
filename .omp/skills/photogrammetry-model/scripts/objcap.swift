// Apple Object Capture CLI (RealityKit PhotogrammetrySession), macOS + Apple Silicon.
// Build: swiftc -O -parse-as-library objcap.swift -o objcap
// Usage: objcap <imagesDir> <outDir> [medium|full|raw|reduced|preview|custom]
//        [--polys N] [--tex 2048|4096|8192] [--no-mask] [--ordering sequential|unordered]
//        [--sensitivity normal|high]
// Writes: <outDir>/model/ (OBJ+MTL+textures), <outDir>/poses.json, <outDir>/bounds.json
import Foundation
import RealityKit
import simd

@main struct ObjCap {
    static func main() async {
        setvbuf(stdout, nil, _IOLBF, 0)   // progress visible when redirected to a log
        var args = Array(CommandLine.arguments.dropFirst())
        guard args.count >= 2 else {
            print("usage: objcap <imagesDir> <outDir> [detail] [--polys N] [--tex 4096] [--no-mask] [--ordering sequential|unordered] [--sensitivity normal|high]")
            exit(2)
        }
        let input = URL(fileURLWithPath: args.removeFirst(), isDirectory: true)
        let outDir = URL(fileURLWithPath: args.removeFirst(), isDirectory: true)
        var detailName = "medium", polys = 0, tex = 4096, mask = true
        var ordering = "unordered", sensitivity = "high"
        var i = 0
        while i < args.count {
            switch args[i] {
            case "--polys": polys = Int(args[i + 1])!; i += 1
            case "--tex": tex = Int(args[i + 1])!; i += 1
            case "--no-mask": mask = false
            case "--ordering": ordering = args[i + 1]; i += 1
            case "--sensitivity": sensitivity = args[i + 1]; i += 1
            default: detailName = args[i]
            }
            i += 1
        }
        let modelDir = outDir.appendingPathComponent("model", isDirectory: true)
        try? FileManager.default.createDirectory(at: modelDir, withIntermediateDirectories: true)

        var config = PhotogrammetrySession.Configuration()
        config.featureSensitivity = sensitivity == "high" ? .high : .normal
        config.sampleOrdering = ordering == "sequential" ? .sequential : .unordered
        config.isObjectMaskingEnabled = mask

        let detail: PhotogrammetrySession.Request.Detail
        switch detailName {
        case "preview": detail = .preview
        case "reduced": detail = .reduced
        case "full": detail = .full
        case "raw": detail = .raw
        case "custom":
            detail = .custom
            var spec = PhotogrammetrySession.Configuration.CustomDetailSpecification()
            spec.maximumPolygonCount = UInt(polys > 0 ? polys : 250_000)
            spec.maximumTextureDimension = tex >= 16384 ? .sixteenK : tex >= 8192 ? .eightK : tex >= 4096 ? .fourK : .twoK
            spec.textureFormat = .png
            spec.outputTextureMaps = [.diffuseColor, .normal]
            config.customDetailSpecification = spec
        default: detail = .medium
        }

        let session: PhotogrammetrySession
        do { session = try PhotogrammetrySession(input: input, configuration: config) }
        catch { print("session error: \(error)"); exit(1) }

        let requests: [PhotogrammetrySession.Request] = [
            .modelFile(url: modelDir, detail: detail), .poses, .bounds,
        ]
        do { try session.process(requests: requests) }
        catch { print("process error: \(error)"); exit(1) }

        var failed = false
        var lastPct = -1
        do {
            for try await output in session.outputs {
                switch output {
                case .inputComplete: print("input complete")
                case .requestProgress(_, let f):
                    let pct = Int(f * 100)
                    if pct / 10 != lastPct / 10 { print("progress \(pct)%"); lastPct = pct }
                case .invalidSample(let id, let reason): print("invalid sample \(id): \(reason)")
                case .skippedSample(let id): print("skipped sample \(id)")
                case .automaticDownsampling: print("automatic downsampling applied")
                case .requestError(let req, let err): print("request error \(req): \(err)"); failed = true
                case .requestComplete(_, let result):
                    switch result {
                    case .modelFile(let url): print("model written: \(url.path)")
                    case .poses(let poses):
                        var arr: [[String: Any]] = []
                        for (id, p) in poses.posesBySample.sorted(by: { $0.key < $1.key }) {
                            let q = p.rotation
                            arr.append([
                                "id": id,
                                "file": poses.urlsBySample[id]?.lastPathComponent ?? "",
                                "t": [p.translation.x, p.translation.y, p.translation.z],
                                "q": [q.imag.x, q.imag.y, q.imag.z, q.real],
                            ])
                        }
                        do {
                            let data = try JSONSerialization.data(withJSONObject: arr, options: [.prettyPrinted])
                            try data.write(to: outDir.appendingPathComponent("poses.json"))
                        } catch { print("poses write error: \(error)") }
                        print("poses: \(arr.count) registered")
                    case .bounds(let b):
                        let j: [String: Any] = ["min": [b.min.x, b.min.y, b.min.z], "max": [b.max.x, b.max.y, b.max.z]]
                        if let d = try? JSONSerialization.data(withJSONObject: j) {
                            try? d.write(to: outDir.appendingPathComponent("bounds.json"))
                        }
                        print("bounds: \(b.min) \(b.max)")
                    default: print("result: \(result)")
                    }
                case .processingComplete:
                    // the outputs stream does not always finish after this; leave explicitly
                    print("processing complete"); exit(failed ? 1 : 0)
                case .processingCancelled: print("cancelled"); failed = true
                case .stitchingIncomplete: print("WARNING: stitching incomplete (some images not connected)")
                default: break
                }
            }
        } catch { print("output error: \(error)"); failed = true }
        exit(failed ? 1 : 0)
    }
}
