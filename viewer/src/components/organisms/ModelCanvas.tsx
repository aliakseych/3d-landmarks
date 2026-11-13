import { useEffect, useLayoutEffect, useMemo, useRef, type MutableRefObject } from "react";
import { Canvas, useThree } from "@react-three/fiber";
import { ContactShadows, Environment, Lightformer, OrbitControls } from "@react-three/drei";
import { Mesh, MathUtils, MeshBasicMaterial, MeshStandardMaterial, Vector3, type Material } from "three";
import type { OrbitControls as OrbitControlsImpl } from "three/addons/controls/OrbitControls.js";
import type { LoadedModel } from "@/lib/model";

export type ViewMode = "textured" | "clay" | "wireframe";

export type CameraApi = { zoom: (factor: number) => void; reset: () => void };

type Props = {
  model: LoadedModel;
  mode: ViewMode;
  autoRotate: boolean;
  apiRef: MutableRefObject<CameraApi | null>;
};

const VIEW_DIRECTION = new Vector3(0.8, 0.45, 1).normalize();

function Model({ model, mode }: Pick<Props, "model" | "mode">) {
  const invalidate = useThree((s) => s.invalidate);
  const clay = useMemo(() => new MeshStandardMaterial({ color: "#d9d3c5", roughness: 0.85, metalness: 0, flatShading: model.stats.triangles < 30000 }), [model]);
  const wire = useMemo(() => new MeshBasicMaterial({ color: "#24506f", wireframe: true }), []);

  useLayoutEffect(() => {
    model.scene.traverse((obj) => {
      if (!(obj instanceof Mesh)) return;
      obj.userData.original ??= obj.material;
      const original = obj.userData.original as Material;
      obj.material = mode === "textured" ? original : mode === "clay" ? clay : wire;
    });
    invalidate();
  }, [model, mode, clay, wire, invalidate]);

  useEffect(
    () => () => {
      clay.dispose();
      wire.dispose();
    },
    [clay, wire],
  );

  return <primitive object={model.scene} />;
}

function Rig({ model, autoRotate, apiRef }: Pick<Props, "model" | "autoRotate" | "apiRef">) {
  const controls = useRef<OrbitControlsImpl>(null);
  const camera = useThree((s) => s.camera);
  const invalidate = useThree((s) => s.invalidate);
  const { center, radius } = model.stats;

  useLayoutEffect(() => {
    const fit = () => {
      const c = controls.current;
      if (!c || !("fov" in camera)) return;
      const persp = camera as typeof camera & { fov: number; aspect: number };
      const vFov = MathUtils.degToRad(persp.fov);
      const hFov = 2 * Math.atan(Math.tan(vFov / 2) * persp.aspect);
      const distance = (radius / Math.sin(Math.min(vFov, hFov) / 2)) * 1.05;
      camera.position.copy(center).addScaledVector(VIEW_DIRECTION, distance);
      persp.near = distance / 100;
      persp.far = distance * 30;
      persp.updateProjectionMatrix();
      c.target.copy(center);
      c.update();
      invalidate();
    };
    const zoom = (factor: number) => {
      const c = controls.current;
      if (!c) return;
      const offset = camera.position.clone().sub(c.target);
      offset.setLength(MathUtils.clamp(offset.length() * factor, c.minDistance, c.maxDistance));
      camera.position.copy(c.target).add(offset);
      c.update();
      invalidate();
    };
    apiRef.current = { zoom, reset: fit };
    fit();
  }, [camera, center, radius, invalidate, apiRef]);

  return (
    <OrbitControls
      ref={controls as never}
      makeDefault
      enableDamping
      dampingFactor={0.08}
      autoRotate={autoRotate}
      autoRotateSpeed={1.5}
      minDistance={radius * 0.5}
      maxDistance={radius * 8}
      maxPolarAngle={Math.PI * 0.495}
    />
  );
}

export function ModelCanvas({ model, mode, autoRotate, apiRef }: Props) {
  const { center, size, minY, radius } = model.stats;
  return (
    <Canvas
      frameloop={autoRotate ? "always" : "demand"}
      dpr={[1, 2]}
      camera={{ fov: 35 }}
      gl={{ antialias: true, powerPreference: "high-performance" }}
      aria-label="Interactive 3D model"
    >
      <hemisphereLight args={["#ffffff", "#cfc8b8", 0.7]} />
      <directionalLight position={[radius * 2, radius * 3, radius * 2]} intensity={1.6} />
      <Environment resolution={256} frames={1} environmentIntensity={0.6}>
        <Lightformer form="rect" intensity={2} position={[0, 5, -6]} scale={[14, 6, 1]} />
        <Lightformer form="rect" intensity={1.2} position={[-6, 2, 4]} scale={[6, 6, 1]} />
        <Lightformer form="rect" intensity={1} position={[6, 1, 4]} scale={[6, 6, 1]} />
      </Environment>
      <Model model={model} mode={mode} />
      <ContactShadows
        key={model.url}
        frames={1}
        position={[center.x, minY - 0.005, center.z]}
        scale={Math.max(size.x, size.z) * 3}
        far={size.y * 1.2}
        blur={2.6}
        opacity={0.5}
        resolution={1024}
      />
      <Rig model={model} autoRotate={autoRotate} apiRef={apiRef} />
    </Canvas>
  );
}
