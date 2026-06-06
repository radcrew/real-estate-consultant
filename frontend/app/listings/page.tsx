import { ButtonPrimary } from "@components/ui/voyager/button-primary";
import { featuredToModel } from "@components/voyager/listing-model";
import { SectionGridFeatureProperty } from "@components/voyager/section-grid-feature-property";
import { brand } from "@config/brand";
import { FEATURED_LISTINGS } from "@constants";

const FEATURED_MODELS = FEATURED_LISTINGS.map(featuredToModel);

const ListingsIndexPage = () => (
  <div className="mx-auto max-w-screen-xl px-4 py-16 lg:py-20">
    <div className="flex flex-col items-start gap-6 border-b border-neutral-200 pb-12 lg:flex-row lg:items-end lg:justify-between dark:border-neutral-700">
      <div className="max-w-2xl">
        <h1 className="text-3xl font-semibold text-neutral-900 md:text-4xl dark:text-neutral-100">
          {brand.sections.listings.heading}
        </h1>
        <p className="mt-3 text-base text-neutral-500 md:text-lg dark:text-neutral-400">
          {brand.sections.listings.subHeading} Start an AI-guided search to see
          properties matched to your needs.
        </p>
      </div>
      <ButtonPrimary
        href="/questionnaire"
        sizeClass="px-7 py-3.5"
        fontSize="text-base font-medium"
      >
        Start searching
      </ButtonPrimary>
    </div>

    <SectionGridFeatureProperty
      className="pt-12"
      heading={brand.sections.featured.heading}
      subHeading={
        <span className="mt-3 block text-neutral-500 dark:text-neutral-400">
          {brand.sections.featured.subHeading}
        </span>
      }
      data={FEATURED_MODELS}
    />
  </div>
);

export default ListingsIndexPage;
