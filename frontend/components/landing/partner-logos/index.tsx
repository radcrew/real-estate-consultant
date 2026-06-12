import Image from "next/image";

/**
 * Partner/trust logos row, ported from Voyager's home-2 `ncSectionLogos` block.
 * Each logo has a light + dark variant; Voyager's display order is 1,4,2,3,5.
 */
const LOGOS = [
  { id: "1", width: 596, height: 150 },
  { id: "4", width: 582, height: 150 },
  { id: "2", width: 550, height: 200 },
  { id: "3", width: 502, height: 186 },
  { id: "5", width: 724, height: 150 },
] as const;

export const PartnerLogos = () => (
  <div className="grid grid-cols-3 gap-5 sm:gap-16 lg:grid-cols-5">
    {LOGOS.map((logo) => (
      <div key={logo.id} className="flex items-end justify-center">
        <Image
          className="block h-7 w-auto object-contain sm:h-9 dark:hidden"
          src={`/images/logos/normal/${logo.id}.png`}
          width={logo.width}
          height={logo.height}
          alt=""
          aria-hidden
        />
        <Image
          className="hidden h-7 w-auto object-contain sm:h-9 dark:block"
          src={`/images/logos/dark/${logo.id}.png`}
          width={logo.width}
          height={logo.height}
          alt=""
          aria-hidden
        />
      </div>
    ))}
  </div>
);
