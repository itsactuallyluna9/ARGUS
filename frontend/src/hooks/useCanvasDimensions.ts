import { useState, useEffect } from "react";

type CanvasDimensions = {
  width: number;
  height: number;
};

const STORAGE_KEY = "argus_canvas_dimensions";
const DEFAULT_DIMENSIONS: CanvasDimensions = {
  width: 504,
  height: 504,
};

export function useCanvasDimensions() {
  const [dimensions, setDimensions] = useState<CanvasDimensions>(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      try {
        return JSON.parse(stored);
      } catch {
        return DEFAULT_DIMENSIONS;
      }
    }
    return DEFAULT_DIMENSIONS;
  });

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(dimensions));
  }, [dimensions]);

  const setWidth = (width: number) => {
    setDimensions((prev) => ({ ...prev, width }));
  };

  const setHeight = (height: number) => {
    setDimensions((prev) => ({ ...prev, height }));
  };

  const reset = () => {
    setDimensions(DEFAULT_DIMENSIONS);
  };

  return {
    dimensions,
    setWidth,
    setHeight,
    reset,
  };
}
