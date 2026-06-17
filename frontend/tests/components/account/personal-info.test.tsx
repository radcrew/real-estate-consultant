// @vitest-environment jsdom
import { render, screen, fireEvent } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { AccountPersonalInfoSection } from "@components/account/sections/personal-info";

vi.mock("next/image", () => ({
  default: ({ alt, src }: { alt: string; src: string }) => <img alt={alt} src={src} />,
}));

const BASE = {
  editing: false,
  values: {
    firstName: "Jane",
    lastName: "Doe",
    email: "jane@example.com",
    phone: "512-555-1234",
    address: "1 Main St",
    city: "Austin",
    state: "TX",
    zipCode: "78701",
    country: "US",
  },
  errors: {},
  onEdit: vi.fn(),
  onCancel: vi.fn(),
  onSave: vi.fn(),
  onChangeField: vi.fn(),
};

describe("AccountPersonalInfoSection", () => {
  it("renders the section heading", () => {
    render(<AccountPersonalInfoSection {...BASE} />);
    expect(screen.getByRole("heading", { name: /personal information/i })).toBeInTheDocument();
  });

  it("shows Edit button when not editing", () => {
    render(<AccountPersonalInfoSection {...BASE} />);
    expect(screen.getByRole("button", { name: /edit/i })).toBeInTheDocument();
  });

  it("calls onEdit when Edit button clicked", () => {
    const onEdit = vi.fn();
    render(<AccountPersonalInfoSection {...BASE} onEdit={onEdit} />);
    fireEvent.click(screen.getByRole("button", { name: /edit/i }));
    expect(onEdit).toHaveBeenCalledTimes(1);
  });

  it("shows Save/Cancel when editing", () => {
    render(<AccountPersonalInfoSection {...BASE} editing={true} />);
    expect(screen.getByRole("button", { name: /save/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /cancel/i })).toBeInTheDocument();
  });

  it("renders error notice with alert role", () => {
    render(<AccountPersonalInfoSection {...BASE} notice="Something went wrong" noticeVariant="error" />);
    expect(screen.getByRole("alert")).toHaveTextContent("Something went wrong");
  });

  it("renders success notice with status role", () => {
    render(<AccountPersonalInfoSection {...BASE} notice="Saved!" noticeVariant="success" />);
    expect(screen.getByRole("status")).toHaveTextContent("Saved!");
  });

  it("renders location line from city and state", () => {
    render(<AccountPersonalInfoSection {...BASE} />);
    expect(screen.getByText("Austin, TX")).toBeInTheDocument();
  });
});
