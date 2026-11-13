import { Camera, Box, Compass, Wand2, Map } from "lucide-react";

const steps = [
  { icon: Camera, title: "Photos", text: "Dozens of overlapping photos walked around the landmark." },
  { icon: Box, title: "Apple Object Capture", text: "Photogrammetry turns the photos into a textured 3D mesh." },
  { icon: Compass, title: "Georeferenced", text: "Scale, orientation and position come from the GPS in the photos." },
  { icon: Wand2, title: "Blender cleanup", text: "Stray geometry removed, base flattened, axes set to metres, +Y up." },
  { icon: Map, title: "Yandex Maps version", text: "A closed, untextured low-poly mesh of at most 15k triangles." },
];

export function HowItsMade() {
  return (
    <ol className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
      {steps.map((s, i) => (
        <li key={s.title} className="flex flex-col gap-2 rounded-xl border border-border bg-card p-4">
          <span className="flex items-center gap-2 text-xs font-medium text-accent">
            <s.icon className="size-4" aria-hidden="true" /> Step {i + 1}
          </span>
          <h3 className="font-semibold">{s.title}</h3>
          <p className="text-sm text-muted-foreground">{s.text}</p>
        </li>
      ))}
    </ol>
  );
}
