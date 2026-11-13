import type { ModelVersion, Place } from "./types";
import { amirTemurPhotos, forumsPalacePhotos } from "./photos";

const yandexMapsUrl = (lat: number, lon: number) =>
  `https://yandex.com/maps/?ll=${lon},${lat}&z=18&pt=${lon},${lat},pm2rdm&l=map`;

function versions(slug: string): ModelVersion[] {
  const m = `models/${slug}`;
  return [
    {
      id: "master",
      label: "Textured master (photogrammetry)",
      hint: "Full-resolution photogrammetry mesh with its 4K photo texture.",
      url: `${m}/${slug}.glb`,
      files: [{ format: "GLB", url: `${m}/${slug}.glb` }],
      textured: true,
    },
    {
      id: "yandex",
      label: "Yandex Maps (low-poly)",
      hint: "Untextured, closed, flat-based mesh of at most 15k triangles for map use.",
      url: `${m}/yandex/${slug}_yandex.glb`,
      files: [
        { format: "GLB", url: `${m}/yandex/${slug}_yandex.glb` },
        { format: "OBJ", url: `${m}/yandex/${slug}_yandex.obj` },
        { format: "FBX", url: `${m}/yandex/${slug}_yandex.fbx` },
      ],
      textured: false,
    },
  ];
}

export const places: Place[] = [
  {
    slug: "amir-temur",
    name: "Amir Temur monument",
    tagline: "Bronze equestrian statue in the central square of Tashkent",
    localNames: { uz: "Amir Temur haykali", ru: "Памятник Эмиру Тимуру" },
    location: {
      lat: 41.3111744,
      lon: 69.2797594,
      address: "Amir Temur Square, Tashkent, Uzbekistan",
      yandexMapsUrl: yandexMapsUrl(41.3111744, 69.2797594),
    },
    description: [
      "The monument shows Amir Temur (Tamerlane), the 14th-century ruler and commander regarded as one of the founders of Uzbek statehood, sitting on a horse. He wears full campaign dress and a helmet shaped like a royal crown, with a sabre at his belt and a shield tied to the saddle. His left hand holds the reins and his right hand is raised.",
      "The bronze statue is the work of the sculptors Ilkhom and Kamol Jabbarov. It was unveiled on 31 August 1993 in the middle of Tashkent, in the square that had just been named after Temur, during celebrations of the second anniversary of Uzbekistan's independence. The pedestal carries his name, AMIR TEMUR, and his motto \"Strength is in justice\" in Uzbek, Russian, English and Arabic.",
      "The square has changed names with each era. It began as a park of the Russian Turkestan period, later became Revolution Square, held statues of Stalin and then Karl Marx, and was renamed after Temur following independence. The statue also appears on Uzbek banknotes, coins and postage stamps, including the 500 sum note of 1999.",
    ],
    facts: [
      { label: "Unveiled", value: "31 August 1993" },
      { label: "Sculptors", value: "Ilkhom and Kamol Jabbarov" },
      { label: "Material", value: "Bronze" },
      { label: "Motto on the pedestal", value: "\"Strength is in justice\"" },
      { label: "Setting", value: "Amir Temur Square, central Tashkent" },
      { label: "Square laid out", value: "1882 (Nikolai Ulyanov)" },
    ],
    sources: [
      { label: "Russian Wikipedia: Памятник Эмиру Тимуру (Ташкент)", url: "https://ru.wikipedia.org/wiki/Памятник_Эмиру_Тимуру_(Ташкент)" },
      { label: "English Wikipedia: Amir Timur Square", url: "https://en.wikipedia.org/wiki/Amir_Timur_Square" },
      { label: "Russian Wikipedia: Сквер Амира Тимура", url: "https://ru.wikipedia.org/wiki/Сквер_Амира_Тимура" },
    ],
    photos: amirTemurPhotos,
    versions: versions("amir-temur"),
  },
  {
    slug: "forums-palace",
    name: "Palace of International Forums \"Uzbekistan\"",
    tagline: "Domed conference palace beside Amir Temur Square",
    localNames: {
      uz: "Oʻzbekiston xalqaro anjumanlar saroyi",
      ru: "Дворец международных форумов «Узбекистан»",
    },
    location: {
      lat: 41.3095402,
      lon: 69.2825796,
      address: "Istiqbol Street, Tashkent, Uzbekistan",
      yandexMapsUrl: yandexMapsUrl(41.3095402, 69.2825796),
    },
    description: [
      "The palace was built to mark the 2,200th anniversary of Tashkent, following a presidential decision of 5 June 2008. Construction ran from May 2008 to July 2009, and it opened on 28 August 2009 with President Islam Karimov, who called it another symbol of the creative power of the people. Local builders carried out the work, the interior fit-out was handled by specialists from Germany and the exterior by specialists from Greece.",
      "It hosts national events, receptions and meetings of international organisations. The building covers more than 9,500 square metres and has a large main hall plus two halls of 300 seats each. A tall colonnade decorates the front, and a dome about 52 metres across crowns it, topped by a sculpture of storks as a symbol of peace and happiness. The facade uses modern materials, white marble and plenty of glass.",
      "Oriental carved patterns and a sun motif echoing the ceiling of the Sher-Dor madrasa in Samarkand decorate the exterior. Visitors enter up long black-marble staircases through gardens and fountains. Inside, the walls use more than 1,300 metres of Swarovski wallpaper, and two chandeliers hold 1,600 individual crystals each.",
    ],
    facts: [
      { label: "Opened", value: "28 August 2009" },
      { label: "Built", value: "May 2008 – July 2009" },
      { label: "Occasion", value: "2,200th anniversary of Tashkent" },
      { label: "Height", value: "48 m" },
      { label: "Dome diameter", value: "about 52 m" },
      { label: "Floor area", value: "over 9,500 m²" },
    ],
    sources: [
      { label: "Uzbek Wikipedia: Oʻzbekiston xalqaro anjumanlar saroyi", url: "https://uz.wikipedia.org/wiki/Oʻzbekiston_xalqaro_anjumanlar_saroyi" },
      { label: "Wikimedia Commons category", url: "https://commons.wikimedia.org/wiki/Category:Palace_of_International_Forums_Uzbekistan" },
      { label: "Coordinates: OpenStreetMap", url: "https://www.openstreetmap.org/?mlat=41.3095402&mlon=69.2825796#map=18/41.3095402/69.2825796" },
    ],
    photos: forumsPalacePhotos,
    versions: versions("forums-palace"),
  },
];

export const findPlace = (slug: string) => places.find((p) => p.slug === slug);
