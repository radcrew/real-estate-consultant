import type { Metadata } from "next";

import { BLOG_POSTS } from "@components/blog/data";
import { BlogFeaturedCard } from "@components/blog/featured-card";
import { BlogPostCard } from "@components/blog/post-card";

export const metadata: Metadata = {
  title: "Insights",
  description: "Commercial real estate insights, market intelligence, and guides from RadEstate.",
};

const [featured, ...rest] = BLOG_POSTS;

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

    {featured ? (
      <div className="mt-12">
        <BlogFeaturedCard post={featured} />
      </div>
    ) : null}

    {rest.length > 0 ? (
      <div className="mt-16 grid grid-cols-1 gap-x-6 gap-y-12 border-t border-neutral-200 pt-16 sm:grid-cols-2 lg:grid-cols-3 lg:gap-x-8 dark:border-neutral-700">
        {rest.map((post) => (
          <BlogPostCard key={post.slug} post={post} />
        ))}
      </div>
    ) : null}
  </div>
);

export default BlogPage;
