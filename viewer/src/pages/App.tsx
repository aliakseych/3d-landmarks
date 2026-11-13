import { findPlace, places } from "@/data/places";
import { useHashRoute } from "@/hooks/useHashRoute";
import { SiteHeader } from "@/components/organisms/SiteHeader";
import { SiteFooter } from "@/components/organisms/SiteFooter";
import { ModelViewer } from "@/components/organisms/ModelViewer";
import { PlaceInfo } from "@/components/organisms/PlaceInfo";
import { PhotoGallery } from "@/components/organisms/PhotoGallery";
import { HowItsMade } from "@/components/organisms/HowItsMade";
import { Section } from "@/components/templates/Section";

export function App() {
  const { route, selectPlace, selectVersion } = useHashRoute();
  const place = findPlace(route.slug) ?? places[0];

  return (
    <div className="flex min-h-dvh flex-col">
      <SiteHeader slug={place.slug} onSelect={selectPlace} />
      <main className="flex-1">
        <div className="mx-auto max-w-6xl px-4 pt-8 sm:px-6">
          <h1 className="text-3xl font-semibold tracking-tight text-balance sm:text-4xl">{place.name}</h1>
          <p className="mt-1 text-muted-foreground">{place.tagline}</p>
          <p className="mt-1 text-sm text-muted-foreground">
            {place.localNames.uz} · {place.localNames.ru}
          </p>
        </div>
        <Section title="3D model">
          <ModelViewer key={place.slug} place={place} versionId={route.version} onVersionChange={selectVersion} />
        </Section>
        <Section title="About">
          <PlaceInfo place={place} />
        </Section>
        <Section title="Photos">
          <PhotoGallery key={place.slug} place={place} />
        </Section>
        <Section title="How the models were made">
          <HowItsMade />
        </Section>
      </main>
      <SiteFooter />
    </div>
  );
}
