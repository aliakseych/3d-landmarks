export type Photo = {
  /** Path relative to the site root, e.g. photos/amir-temur/01.jpg */
  src: string;
  caption: string;
  width: number;
  height: number;
  author: string;
  license: string;
  licenseUrl: string;
  /** Wikimedia Commons file page */
  source: string;
};

export type ModelFile = { format: "GLB" | "OBJ" | "FBX"; url: string };

export type ModelVersionId = "master" | "yandex";

export type ModelVersion = {
  id: ModelVersionId;
  label: string;
  hint: string;
  /** File the viewer loads */
  url: string;
  /** Files offered for download (the first is the loaded GLB) */
  files: ModelFile[];
  /** Whether the file carries its own texture/material */
  textured: boolean;
};

export type Fact = { label: string; value: string };

export type SourceLink = { label: string; url: string };

export type Place = {
  slug: string;
  name: string;
  tagline: string;
  localNames: { uz: string; ru: string };
  location: { lat: number; lon: number; address: string; yandexMapsUrl: string };
  description: string[];
  facts: Fact[];
  sources: SourceLink[];
  photos: Photo[];
  versions: ModelVersion[];
};
