import { Accuse } from "@/widgets/accuse";

export default async function Page({ params }: PageProps<"/cases/[number]/accuse">) {
  const { number } = await params;
  return <Accuse caseNumber={Number(number)} />;
}
