import type { QuickSearchBody } from "@services/search";

export type Category = {
  id: string;
  name: string;
  search: QuickSearchBody;
  thumbnail: string;
};

/** Slider 1 — "Suggestions for discovery" (markets). */
export const DISCOVERY_CATEGORIES: Category[] = [
  {
    id: "1",
    name: "Chicago Metro",
    search: { location: "Chicago, IL" },
    thumbnail:
      "https://images.pexels.com/photos/5764100/pexels-photo-5764100.jpeg?auto=compress&cs=tinysrgb&dpr=3&h=750&w=1260",
  },
  {
    id: "2",
    name: "Northwest Indiana",
    search: { location: "Gary, IN" },
    thumbnail:
      "https://images.pexels.com/photos/2869499/pexels-photo-2869499.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=750&w=1260",
  },
  {
    id: "3",
    name: "Indianapolis Metro",
    search: { location: "Indianapolis, IN" },
    thumbnail:
      "https://images.pexels.com/photos/7031413/pexels-photo-7031413.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=750&w=1260",
  },
  {
    id: "4",
    name: "Western Suburbs",
    search: { location: "Naperville, IL" },
    thumbnail:
      "https://images.pexels.com/photos/247532/pexels-photo-247532.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=750&w=1260",
  },
  {
    id: "5",
    name: "O'Hare Corridor",
    search: { location: "Schaumburg, IL" },
    thumbnail:
      "https://images.pexels.com/photos/7031413/pexels-photo-7031413.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=750&w=1260",
  },
  {
    id: "6",
    name: "South Suburbs",
    search: { location: "Joliet, IL" },
    thumbnail:
      "https://images.pexels.com/photos/2869499/pexels-photo-2869499.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=750&w=1260",
  },
];

/** Slider 2 — "Explore by property type". */
export const PROPERTY_TYPE_CATEGORIES: Category[] = [
  {
    id: "1",
    name: "Industrial",
    search: { property_types: ["Industrial"] },
    thumbnail:
      "https://images.pexels.com/photos/2581922/pexels-photo-2581922.jpeg?auto=compress&cs=tinysrgb&dpr=3&h=750&w=1260",
  },
  {
    id: "2",
    name: "Flex",
    search: { property_types: ["Flex"] },
    thumbnail:
      "https://images.pexels.com/photos/2351649/pexels-photo-2351649.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=750&w=1260",
  },
  {
    id: "3",
    name: "Retail",
    search: { property_types: ["Retail"] },
    thumbnail:
      "https://images.pexels.com/photos/962464/pexels-photo-962464.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=750&w=1260",
  },
  {
    id: "4",
    name: "Office",
    search: { property_types: ["Office"] },
    thumbnail:
      "https://images.pexels.com/photos/248837/pexels-photo-248837.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=750&w=1260",
  },
  {
    id: "5",
    name: "Cold Storage",
    search: { property_types: ["Cold Storage"] },
    thumbnail:
      "https://images.pexels.com/photos/3613236/pexels-photo-3613236.jpeg?auto=compress&cs=tinysrgb&dpr=1&w=500",
  },
  {
    id: "6",
    name: "Land",
    search: { property_types: ["Land"] },
    thumbnail:
      "https://images.pexels.com/photos/14534337/pexels-photo-14534337.jpeg?auto=compress&cs=tinysrgb&w=1600&lazy=load",
  },
  {
    id: "7",
    name: "Medical",
    search: { property_types: ["Medical"] },
    thumbnail:
      "https://images.pexels.com/photos/2351649/pexels-photo-2351649.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=750&w=1260",
  },
  {
    id: "8",
    name: "Manufacturing",
    search: { property_types: ["Manufacturing"] },
    thumbnail:
      "https://images.pexels.com/photos/9039238/pexels-photo-9039238.jpeg?auto=compress&cs=tinysrgb&w=1600&lazy=load",
  },
];
