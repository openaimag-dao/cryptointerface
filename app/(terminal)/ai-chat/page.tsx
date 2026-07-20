import { Card } from "@/components/ui/card";
import { ChatSidebar } from "@/components/chat/chat-sidebar";
import { ChatWindow } from "@/components/chat/chat-window";

export default function AiChatPage() {
  return (
    <Card className="flex h-[calc(100vh-7rem)] overflow-hidden p-0">
      <ChatSidebar />
      <ChatWindow />
    </Card>
  );
}
