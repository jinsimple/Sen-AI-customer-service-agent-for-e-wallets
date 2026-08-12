import { describe, expect, it } from "vitest";
import { parseSessionCookie, roleHome } from "./session";

describe("roleHome", () => {
  it.each([
    ["customer", "/chat"],
    ["cskh", "/dashboard"],
    ["partner_admin", "/knowledge"],
    ["supervisor", "/approve"],
  ] as const)("role=%s -> %s", (role, expected) => {
    expect(roleHome(role)).toBe(expected);
  });
});

describe("parseSessionCookie", () => {
  const validSession = {
    user_id: "USR-A",
    role: "customer",
    full_name: "Nguyễn Văn A",
    phone: "0901000001",
    access_token: "fake.jwt.token",
  };

  it("parse đúng cookie hợp lệ", () => {
    const result = parseSessionCookie(JSON.stringify(validSession));
    expect(result).toEqual(validSession);
  });

  it("trả null khi cookie undefined", () => {
    expect(parseSessionCookie(undefined)).toBeNull();
  });

  it("trả null khi JSON hỏng (không throw ra ngoài)", () => {
    expect(parseSessionCookie("{không phải json hợp lệ")).toBeNull();
  });

  it("trả null khi thiếu field bắt buộc (access_token)", () => {
    const missingToken: Record<string, unknown> = { ...validSession };
    delete missingToken.access_token;
    expect(parseSessionCookie(JSON.stringify(missingToken))).toBeNull();
  });

  it("trả null khi role không nằm trong danh sách hợp lệ", () => {
    expect(parseSessionCookie(JSON.stringify({ ...validSession, role: "admin_bịa" }))).toBeNull();
  });
});
