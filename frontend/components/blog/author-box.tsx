import { Avatar } from "@components/ui/avatar";
import type { BlogAuthor } from "@components/blog/data";

/**
 * Voyager-style author card shown at the end of a blog post: avatar plus the
 * author's name, role and bio in a bordered card.
 */
type BlogAuthorBoxProps = {
  author: BlogAuthor;
};

export const BlogAuthorBox = ({ author }: BlogAuthorBoxProps) => (
  <div className="flex flex-col gap-5 rounded-3xl border border-neutral-200 p-6 sm:flex-row sm:p-8 dark:border-neutral-700">
    <Avatar
      userName={author.name}
      sizeClass="h-16 w-16 text-xl"
      radius="rounded-full"
      containerClassName="shrink-0"
    />
    <div className="min-w-0">
      <p className="text-xs font-semibold uppercase tracking-wide text-primary-600 dark:text-primary-400">
        {author.role}
      </p>
      <h3 className="mt-1 text-lg font-semibold text-neutral-900 dark:text-neutral-100">
        {author.name}
      </h3>
      {author.bio ? (
        <p className="mt-2 text-sm leading-relaxed text-neutral-600 dark:text-neutral-300">
          {author.bio}
        </p>
      ) : null}
    </div>
  </div>
);
