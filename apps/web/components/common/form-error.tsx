import { Alert } from "@/components/ui/alert";

type FormErrorProps = {
  message?: string | null;
};

export function FormError({ message }: FormErrorProps) {
  if (!message) {
    return null;
  }

  return <Alert variant="error">{message}</Alert>;
}
