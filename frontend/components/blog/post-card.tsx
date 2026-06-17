import Image from "next/image";
import Link from "next/link";

import { Avatar } from "@components/ui/avatar";
import { Badge } from "@components/ui/badge";

import type { BlogPost } from "./data";

/**
 * Blog post card, in Voyager's post-card style: rounded cover, category badge,
 * title, excerpt, and an author/date meta row.
 */
type BlogPostCardProps = {
  post: BlogPost;
};

export const BlogPostCard = ({ post }: BlogPostCardProps) => (
  <Link
    href={`/blog/${post.slug}`}
    className="group flex flex-col overflow-hidden rounded-2xl border border-neutral-200 bg-white shadow-sm transition-shadow duration-300 hover:shadow-lg dark:border-neutral-700 dark:bg-neutral-900"
  >
    <div className="relative aspect-[16/10] overflow-hidden bg-neutral-100 dark:bg-neutral-800">
      <Image
        src={post.image}
        alt={post.title}
        fill
        sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 33vw"
        className="object-cover transition-transform duration-300 group-hover:scale-105"
      />
    </div>
    <div className="flex flex-1 flex-col p-5">
      <Badge name={post.category} color="indigo" className="self-start" />
      <h3 className="mt-3 text-lg font-semibold text-neutral-900 group-hover:text-primary-600 dark:text-neutral-100">
        <span className="line-clamp-2">{post.title}</span>
      </h3>
      <p className="mt-2 line-clamp-2 text-sm text-neutral-500 dark:text-neutral-400">
        {post.excerpt}
      </p>
      <div className="mt-4 flex items-center gap-2.5 text-sm text-neutral-500 dark:text-neutral-400">
        <Avatar userName={post.author} sizeClass="h-7 w-7 text-xs" />
        <span className="text-neutral-700 dark:text-neutral-300">{post.author}</span>
        <span aria-hidden>·</span>
        <span>{post.date}</span>
      </div>
    </div>
  </Link>
);
