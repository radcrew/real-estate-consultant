type ListingPageProps = { params: Promise<{ id: string }> }

const ListingPage = async ({ params }: ListingPageProps) => {
  const { id } = await params
  return (
    <div className="mx-auto max-w-screen-xl px-4 py-16">
      <h1 className="text-2xl font-bold text-foreground">Listing {id}</h1>
      <p className="mt-2 text-muted-foreground">Detail view coming soon.</p>
    </div>
  )
}

export default ListingPage
