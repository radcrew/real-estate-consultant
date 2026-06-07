export type BlogPost = {
  slug: string;
  title: string;
  excerpt: string;
  /** Body paragraphs, rendered on the post detail page. */
  content: string[];
  category: string;
  author: string;
  date: string;
  readingTime: string;
  image: string;
};

export const BLOG_POSTS: BlogPost[] = [
  {
    slug: "industrial-demand-2026",
    title: "Why industrial demand keeps outpacing supply in 2026",
    excerpt:
      "Last-mile logistics and reshoring are reshaping where tenants want space — and how fast it leases.",
    content: [
      "Industrial remains the standout asset class heading into 2026. Vacancy in core distribution corridors stays tight as third-party logistics providers and retailers compete for the same modern, high-clear-height buildings.",
      "For occupiers, that means moving earlier in the process. Tour-ready buildings with 32'+ clear heights, ample dock doors, and trailer parking are leasing within weeks of hitting the market.",
      "The takeaway: define your must-haves up front, get your search criteria scored, and be ready to act when a fit appears.",
    ],
    category: "Market Intelligence",
    author: "Alex Morgan",
    date: "May 28, 2026",
    readingTime: "5 min read",
    image:
      "https://images.pexels.com/photos/2506988/pexels-photo-2506988.jpeg?auto=compress&cs=tinysrgb&w=900",
  },
  {
    slug: "clear-height-matters",
    title: "Clear height, explained: what to verify before you tour",
    excerpt:
      "Listed clear heights are often inferred. Here's how to confirm the number that actually affects your racking.",
    content: [
      "Clear height is one of the most consequential — and most frequently misstated — specs in industrial real estate. The difference between 28' and 32' can change your storage capacity by double digits.",
      "Always confirm whether a listed clear height is measured or inferred, and where it's measured (at the eave vs. under the lowest obstruction).",
      "RadEstate flags when a clear height is inferred versus confirmed, so there are no surprises on tour.",
    ],
    category: "Guides",
    author: "Tom Whitfield",
    date: "May 14, 2026",
    readingTime: "4 min read",
    image:
      "https://images.pexels.com/photos/4577673/pexels-photo-4577673.jpeg?auto=compress&cs=tinysrgb&w=900",
  },
  {
    slug: "retail-corners-comeback",
    title: "The quiet comeback of high-street retail corners",
    excerpt:
      "Experiential and service tenants are paying up for visibility. What that means for corner suites.",
    content: [
      "After several uneven years, well-located retail corners are seeing renewed demand from service, medical, and experiential tenants who value foot traffic and signage.",
      "Pricing power has returned to landlords in the best locations, while secondary corridors still favor tenants.",
      "If you're hunting for retail, location specificity is everything — narrow your submarkets before you compare deals.",
    ],
    category: "Market Intelligence",
    author: "Priya Patel",
    date: "April 30, 2026",
    readingTime: "6 min read",
    image:
      "https://images.pexels.com/photos/6474535/pexels-photo-6474535.jpeg?auto=compress&cs=tinysrgb&w=900",
  },
  {
    slug: "broker-outreach-that-works",
    title: "Broker outreach that actually gets a reply",
    excerpt:
      "A short, specific first message beats a long one. Here's a template that respects everyone's time.",
    content: [
      "The best outreach is specific: name the property, your requirement, and your timeline in a few sentences.",
      "Brokers respond to qualified, concrete interest. Vague 'send me everything' requests get deprioritized.",
      "RadEstate drafts outreach you can edit and send yourself — you stay in control of the relationship.",
    ],
    category: "Guides",
    author: "Emily Carter",
    date: "April 12, 2026",
    readingTime: "3 min read",
    image:
      "https://images.pexels.com/photos/3201735/pexels-photo-3201735.jpeg?auto=compress&cs=tinysrgb&w=900",
  },
];

export const getBlogPost = (slug: string): BlogPost | undefined =>
  BLOG_POSTS.find((p) => p.slug === slug);
