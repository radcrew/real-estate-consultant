import type { Metadata } from "next";
import Image from "next/image";
import Link from "next/link";
import { notFound } from "next/navigation";
import { ArrowLeft } from "lucide-react";

import { BLOG_POSTS, getBlogAuthor, getBlogPost } from "@components/blog/data";
import { BlogAuthorBox } from "@components/blog/author-box";
import { BlogPostCard } from "@components/blog/post-card";
import { Avatar } from "@components/ui/avatar";
import { Badge } from "@components/ui/badge";

type BlogPostPageProps = {
  params: Promise<{ slug: string }>;
};

export const generateStaticParams = () =>
  BLOG_POSTS.map((post) => ({ slug: post.slug }));

export const generateMetadata = async ({
  params,
}: BlogPostPageProps): Promise<Metadata> => {
  const { slug } = await params;
  const post = getBlogPost(slug);
  if (!post) {
    return { title: "Article not found" };
  }
  return { title: post.title, description: post.excerpt };
};

const BlogPostPage = async ({ params }: BlogPostPageProps) => {
  const { slug } = await params;
  const post = getBlogPost(slug);
  if (!post) {
    notFound();
  }

  const related = BLOG_POSTS.filter((p) => p.slug !== post.slug).slice(0, 3);

  return (
    <div className="pb-16 lg:pb-24">
      <header className="mx-auto max-w-3xl px-4 pt-10 lg:pt-16">
        <Link
          href="/blog"
          className="inline-flex items-center gap-2 text-sm font-medium text-neutral-500 hover:text-neutral-900 dark:text-neutral-400 dark:hover:text-white"
        >
          <ArrowLeft className="size-4" aria-hidden />
          All insights
        </Link>

        <div className="mt-6">
          <Badge name={post.category} color="indigo" />
        </div>
        <h1 className="mt-4 text-3xl font-semibold leading-tight text-neutral-900 md:text-4xl dark:text-neutral-100">
          {post.title}
        </h1>
        <div className="mt-6 flex items-center gap-3 text-sm text-neutral-500 dark:text-neutral-400">
          <Avatar userName={post.author} sizeClass="h-9 w-9 text-sm" />
          <span className="font-medium text-neutral-700 dark:text-neutral-200">
            {post.author}
          </span>
          <span aria-hidden>·</span>
          <span>{post.date}</span>
          <span aria-hidden>·</span>
          <span>{post.readingTime}</span>
        </div>
      </header>

      <div className="relative mx-auto mt-10 aspect-[16/9] max-w-4xl overflow-hidden px-4 sm:rounded-3xl">
        <Image
          src={post.image}
          alt={post.title}
          fill
          priority
          sizes="(max-width: 896px) 100vw, 896px"
          className="object-cover sm:rounded-3xl"
        />
      </div>

      <article className="mx-auto mt-10 max-w-3xl space-y-6 px-4 text-lg leading-relaxed text-neutral-700 dark:text-neutral-300">
        {post.content.map((paragraph, i) => (
          <p key={i}>{paragraph}</p>
        ))}
      </article>

      <div className="mx-auto mt-14 max-w-3xl px-4">
        <BlogAuthorBox author={getBlogAuthor(post.author)} />
      </div>

      {related.length > 0 && (
        <section className="mx-auto mt-20 max-w-screen-xl px-4">
          <h2 className="text-2xl font-semibold text-neutral-900 dark:text-neutral-100">
            More insights
          </h2>
          <div className="mt-8 grid grid-cols-1 gap-x-6 gap-y-12 sm:grid-cols-2 lg:grid-cols-3 lg:gap-x-8">
            {related.map((p) => (
              <BlogPostCard key={p.slug} post={p} />
            ))}
          </div>
        </section>
      )}
    </div>
  );
};

export default BlogPostPage;
