import re
from playwright.sync_api import Playwright, sync_playwright, expect


def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    page.goto("https://dgx.xlook.ai/dgx/f2b850f5-14a0-4325-b56d-cb1213f63ec2")
    page.get_by_role("button", name="Faya Al Saadiyat").nth(1).click()
    page.get_by_role("button", name="Faya Al Saadiyat Go to").click()
    page.get_by_text("Set Boundaries").click()
    page.get_by_role("button", name="UploadPlot CAD File").click()
    page.locator("#headlessui-control-_r_5_").click()
    page.get_by_role("option", name="Not Required").click()
    page.locator("#headlessui-control-_r_d_").click()
    page.get_by_role("button", name="---- Select a Layer ----").click()
    page.locator("#headlessui-control-_r_d_").click()
    page.get_by_label("---- Select a Layer ----").get_by_text("Not Required").click()
    page.locator("#headlessui-control-_r_l_").click()
    page.get_by_label("---- Select a Layer ----").get_by_text("Not Required").click()
    page.get_by_role("button", name="Cancel").click()
    page.get_by_role("main").get_by_text("Next").click()
    page.get_by_role("main").get_by_text("Next").click()
    page.locator("div").filter(has_text=re.compile(r"^Show/Hide All$")).get_by_role("checkbox").uncheck()
    page.locator(".mkb-list-item > input").first.check()
    page.locator(".mkb-list > div:nth-child(2) > input").check()
    page.locator("div").filter(has_text=re.compile(r"^Show/Hide All$")).get_by_role("checkbox").check()
    page.get_by_text("Done").click()
    page.get_by_role("cell", name="Park Hyatt Abu Dhabi Hotel").click()
    page.get_by_role("main").locator("svg").nth(1).click()
    page.locator(".sc-left > .dgx-stepper > div:nth-child(6) > .dgx-step-icon").click()
    page.locator(".sc-left > .dgx-stepper > div:nth-child(8) > .dgx-step-icon").click()

    # ---------------------
    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)
