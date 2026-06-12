import { ImageResponse } from "next/og";

import { brand } from "@config/brand";

// App icon (favicon + tab icon), generated from the brand mark so we don't
// depend on a static asset. Renders the brand initial on Voyager's indigo.
export const size = { width: 32, height: 32 };
export const contentType = "image/png";

const Icon = () =>
  new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          // Voyager primary indigo (primary-600, rgb 79 70 229).
          background: "#4F46E5",
          color: "#ffffff",
          fontSize: 22,
          fontWeight: 700,
          borderRadius: 6,
        }}
      >
        {brand.name.charAt(0)}
      </div>
    ),
    { ...size },
  );

export default Icon;
