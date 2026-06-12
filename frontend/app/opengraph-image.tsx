import { ImageResponse } from "next/og";

import { brand } from "@config/brand";

// Default Open Graph / Twitter card image for link previews, generated from the
// brand so we don't ship a static asset. Routes deeper in the tree can override
// this by adding their own opengraph-image file.
export const alt = `${brand.name} · ${brand.tagline}`;
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

const OpengraphImage = () =>
  new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          padding: "80px",
          // Voyager indigo gradient.
          background: "linear-gradient(135deg, #4F46E5 0%, #6366F1 100%)",
          color: "#ffffff",
          fontFamily: "sans-serif",
        }}
      >
        <div style={{ fontSize: 96, fontWeight: 700, letterSpacing: -2 }}>
          {brand.name}
        </div>
        <div style={{ marginTop: 24, fontSize: 40, opacity: 0.9 }}>
          {brand.tagline}
        </div>
      </div>
    ),
    { ...size },
  );

export default OpengraphImage;
