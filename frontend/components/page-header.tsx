type PageHeaderProps = {
  title: string
  description?: string
}

export function PageHeader({ title, description }: PageHeaderProps) {
  return (
    <div className="mb-6">
      <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">{title}</h1>
      {description ? (
        <p className="mt-1 text-muted-foreground">{description}</p>
      ) : null}
    </div>
  )
}
