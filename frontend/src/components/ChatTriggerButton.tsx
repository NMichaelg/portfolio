"use client";

import { Button } from "@/components/ui/button";
import { useChatWidget } from "@/components/ChatProvider";
import type { ComponentProps } from "react";

export default function ChatTriggerButton({
  children,
  ...props
}: ComponentProps<typeof Button>) {
  const { setOpen } = useChatWidget();
  return (
    <Button onClick={() => setOpen(true)} {...props}>
      {children}
    </Button>
  );
}