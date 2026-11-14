import { CaseCertificate } from "@/widgets/certificate";

export default async function Page({ params }: PageProps<"/cases/[number]/certificate">) {
  const { number } = await params;
  return <CaseCertificate caseNumber={Number(number)} />;
}
