import { places } from "@/data/places";

export function SiteFooter() {
  const link = "underline decoration-border underline-offset-2 hover:text-foreground";
  return (
    <footer className="border-t border-border bg-card">
      <div className="mx-auto flex max-w-6xl flex-col gap-6 px-4 py-10 text-sm text-muted-foreground sm:px-6">
        <h2 className="text-base font-semibold text-foreground">Photo credits and licences</h2>
        <p>Real-world photos come from Wikimedia Commons under the licences listed here. They have been resized; no other changes were made.</p>
        <div className="grid gap-6 md:grid-cols-2">
          {places.map((pl) => (
            <div key={pl.slug}>
              <h3 className="mb-2 font-medium text-foreground">{pl.name}</h3>
              <ul className="flex flex-col gap-1">
                {pl.photos.map((p) => (
                  <li key={p.src}>
                    <a className={link} href={p.source} target="_blank" rel="noreferrer">{p.caption}</a>: {p.author},{" "}
                    <a className={link} href={p.licenseUrl} target="_blank" rel="noreferrer license">{p.license}</a>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
        <p>
          Descriptions are summaries of Wikipedia articles (CC BY-SA). The 3D models are our own work. UI components adapted from a personal component library.
        </p>
      </div>
    </footer>
  );
}
