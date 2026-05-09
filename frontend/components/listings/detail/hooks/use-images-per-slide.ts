"use client";

import { useEffect, useState } from "react";

export function useImagesPerSlide(): number {
  const [n, setN] = useState(1);

  useEffect(() => {
    const read = () => {
      const w = window.innerWidth;
      if (w < 640) {
        setN(1);
      } else if (w < 1024) {
        setN(2);
      } else {
        setN(3);
      }
    };
    read();
    window.addEventListener("resize", read);
    return () => window.removeEventListener("resize", read);
  }, []);

  return n;
}
