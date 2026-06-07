export type AuthorBox = {
  id: string;
  displayName: string;
  jobName: string;
  count: number;
  href: string;
  avatar: string;
  bgImage: string;
};

const BG_IMAGES = [
  "https://images.pexels.com/photos/5764100/pexels-photo-5764100.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=400&w=600",
  "https://images.pexels.com/photos/2869499/pexels-photo-2869499.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=400&w=600",
  "https://images.pexels.com/photos/7031413/pexels-photo-7031413.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=400&w=600",
  "https://images.pexels.com/photos/247532/pexels-photo-247532.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=400&w=600",
];

const NAMES = [
  ["Alex Morgan", "industrial-broker", 132],
  ["Priya Patel", "retail-specialist", 98],
  ["Daniel Cho", "office-leasing", 87],
  ["Maria Santos", "flex-industrial", 76],
  ["James O'Brien", "logistics-broker", 64],
  ["Sara Klein", "investment-sales", 58],
  ["Tom Whitfield", "cold-storage", 51],
  ["Nina Rossi", "land-development", 47],
  ["Marcus Lee", "medical-office", 39],
  ["Emily Carter", "tenant-rep", 34],
] as const;

/** "Top brokers" data — Voyager's author-box concept adapted to CRE brokers. */
export const TOP_BROKERS: AuthorBox[] = NAMES.map(([displayName, jobName, count], i) => ({
  id: String(i + 1),
  displayName,
  jobName,
  count,
  href: "/listings",
  avatar: `/images/avatars/Image-${i + 1}.png`,
  bgImage: BG_IMAGES[i % BG_IMAGES.length],
}));
