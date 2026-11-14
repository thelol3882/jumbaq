import { Evening } from "@/widgets/evening";

export default async function Page({ params }: PageProps<"/cases/[number]/evenings/[evening]">) {
  const { number, evening } = await params;
  return <Evening caseNumber={Number(number)} evening={Number(evening)} />;
}
