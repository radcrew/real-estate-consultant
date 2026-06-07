import Image from "next/image";
import Link from "next/link";

import { Avatar } from "@components/ui/voyager/avatar";
import { Badge } from "@components/ui/voyager/badge";

import type { BlogPost } from "./data";

/**
 * Large lead post card for the blog index (Voyager magazine style): cover on one
 * side, category + title + excerpt + meta on the other.
 */
type BlogFeaturedCardProps = {
  post: BlogPost;
};

export const BlogFeaturedCard = ({ post }: BlogFeaturedCardProps) => (
  <Link
    href={`/blog/${post.slug}`}
    className="group grid gap-6 md:grid-cols-2 md:items-center md:gap-10"
  >
    <div className="relative aspect-[16/10] overflow-hidden rounded-3xl bg-neutral-100 dark:bg-neutral-800">
      <Image
        src={post.image}
        alt={post.title}
        fill
        priority
        sizes="(max-width: 768px) 100vw, 50vw"
        className="object-cover transition-transform duration-300 group-hover:scale-105"
      />
    </div>
    <div>
      <Badge name={post.category} color="indigo" />
      <h2 className="mt-4 text-2xl font-semibold leading-tight text-neutral-900 group-hover:text-primary-600 md:text-3xl dark:text-neutral-100">
        {post.title}
      </h2>
      <p className="mt-3 line-clamp-3 text-neutral-500 dark:text-neutral-400">
        {post.excerpt}
      </p>
      <div className="mt-5 flex items-center gap-2.5 text-sm text-neutral-500 dark:text-neutral-400">
        <Avatar userName={post.author} sizeClass="h-8 w-8 text-xs" />
        <span className="text-neutral-700 dark:text-neutral-300">{post.author}</span>
        <span aria-hidden>·</span>
        <span>{post.date}</span>
        <span aria-hidden>·</span>
        <span>{post.readingTime}</span>
      </div>
    </div>
  </Link>
);
