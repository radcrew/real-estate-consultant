import type { Metadata } from "next";

import { BLOG_POSTS } from "@components/blog/data";
import { BlogPostCard } from "@components/blog/post-card";

export const metadata: Metadata = {
  title: "Insights",
  description: "Commercial real estate insights, market intelligence, and guides from RadEstate.",
};

const BlogPage = () => (
  <div className="mx-auto max-w-screen-xl px-4 py-16 lg:py-20">
    <div className="max-w-2xl">
      <h1 className="text-3xl font-semibold text-neutral-900 md:text-4xl dark:text-neutral-100">
        Insights
      </h1>
      <p className="mt-3 text-neutral-500 dark:text-neutral-400">
        Market intelligence, guides, and commentary for commercial real estate.
      </p>
    </div>

    <div className="mt-12 grid grid-cols-1 gap-x-6 gap-y-12 sm:grid-cols-2 lg:grid-cols-3 lg:gap-x-8">
      {BLOG_POSTS.map((post) => (
        <BlogPostCard key={post.slug} post={post} />
      ))}
    </div>
  </div>
);

export default BlogPage;
