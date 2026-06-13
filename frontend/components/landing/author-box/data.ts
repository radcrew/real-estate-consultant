export type AuthorBox = {
  id: string;
  displayName: string;
  jobName: string;
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
  ["Alex Morgan", "industrial-broker"],
  ["Priya Patel", "retail-specialist"],
  ["Daniel Cho", "office-leasing"],
  ["Maria Santos", "flex-industrial"],
  ["James O'Brien", "logistics-broker"],
  ["Sara Klein", "investment-sales"],
  ["Tom Whitfield", "cold-storage"],
  ["Nina Rossi", "land-development"],
  ["Marcus Lee", "medical-office"],
  ["Emily Carter", "tenant-rep"],
] as const;

export const TOP_BROKERS: AuthorBox[] = NAMES.map(([displayName, jobName], i) => ({
  id: String(i + 1),
  displayName,
  jobName,
  avatar: `/images/avatars/Image-${i + 1}.png`,
  bgImage: BG_IMAGES[i % BG_IMAGES.length],
}));
