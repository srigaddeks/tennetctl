import { Plus } from "lucide-react";
import { PageHeader, PageBody } from "@/components/shell/page-header";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { GroupsTable } from "@/features/iam/_components/groups-table";

export default function IamGroupsPage() {
  return (
    <>
      <PageHeader
        breadcrumb={["IAM", "Groups"]}
        title="Groups"
        description="Named collections of users within an organisation."
        actions={
          <Button size="sm" disabled>
            <Plus /> New group
          </Button>
        }
      />
      <PageBody>
        <Card className="overflow-hidden p-0">
          <GroupsTable />
        </Card>
      </PageBody>
    </>
  );
}
