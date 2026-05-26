export type PartSourceRef = {
  file: string;
  symbol: string | null;
  start_line: number;
  end_line: number;
};

export type ModelPart = {
  id: string;
  label: string;
  color: string;
  stl_url: string;
  opacity?: number;
  source_ref?: PartSourceRef;
};

export type PartsManifest = {
  parts: ModelPart[];
  backend?: string;
};
