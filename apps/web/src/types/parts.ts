export type ModelPart = {
  id: string;
  label: string;
  color: string;
  stl_url: string;
  opacity?: number;
};

export type PartsManifest = {
  parts: ModelPart[];
  backend?: string;
};
