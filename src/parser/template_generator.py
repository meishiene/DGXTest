from __future__ import annotations

from pathlib import Path

from openpyxl import Workbook


DGX_DEMO_ROUTE = "/dgx/f2b850f5-14a0-4325-b56d-cb1213f63ec2"
PLACEHOLDER_REMARK = "Assertion placeholder: fill assert_key, target, expected, and match_type later. Empty placeholder assertions are skipped by the runner."


def generate_excel_templates(test_workbook_path: Path, object_repo_path: Path) -> None:
    test_workbook_path.parent.mkdir(parents=True, exist_ok=True)
    object_repo_path.parent.mkdir(parents=True, exist_ok=True)
    _build_test_workbook().save(test_workbook_path)
    _build_object_workbook().save(object_repo_path)


def _build_test_workbook() -> Workbook:
    workbook = Workbook()

    case_sheet = workbook.active
    case_sheet.title = "Case_Index"
    case_sheet.append([
        "case_id", "case_name", "module", "sub_module", "feature_name", "case_type", "priority",
        "test_level", "tags", "status", "automation_flag", "precondition_id", "preconditions",
        "postconditions", "data_set_id", "env_scope", "browser_scope", "can_parallel", "retry_policy",
        "owner", "require_login", "depends_on_case", "expected_result_summary", "ai_hint", "remark"
    ])
    case_sheet.append([
        "DGX_001", "Open DGX demo and reach Set Boundaries", "DGX", "Demo", "Project Entry", "functional", "P1",
        "smoke", "dgx,demo,entry", "active", "Y", "", "Demo URL is reachable", "", "DATA_DGX_DEFAULT_01",
        "demo", "chromium", "Y", "case_retry_1", "tester", "N", "",
        "Set Boundaries panel is reachable", "Use the recorded DGX design demo flow", "Default DGX demo smoke case"
    ])
    case_sheet.append([
        "DGX_002", "Configure boundary layers and finish setup", "DGX", "Demo", "Boundary Setup", "functional", "P1",
        "smoke", "dgx,demo,boundary", "active", "Y", "", "Boundary setup page is open", "", "DATA_DGX_DEFAULT_01",
        "demo", "chromium", "Y", "case_retry_1", "tester", "N", "",
        "Boundary setup can be completed and the project result is shown", "Derived from the recorded DGX boundary workflow", "Default DGX boundary regression case"
    ])

    step_sheet = workbook.create_sheet("Case_Steps")
    step_sheet.append([
        "case_id", "step_no", "step_type", "step_name", "action_key", "assert_key", "page_name", "target",
        "target_type", "value", "value_type", "expected", "expected_type", "match_type", "wait", "timeout",
        "continue_on_fail", "screenshot_on_fail", "ai_locator_hint", "remark"
    ])
    step_sheet.append(["DGX_001", 1, "action", "Open DGX demo landing page", "open_page", "", "DGXLandingPage", DGX_DEMO_ROUTE, "route", "", "", "", "", "", "dom_ready", 10, "N", "Y", "", ""])
    step_sheet.append(["DGX_001", 2, "action", "Open project card entry button", "click", "", "DGXLandingPage", "project_card_entry_button", "element", "", "", "", "", "", "visible", 10, "N", "Y", "Faya entry button", ""])
    step_sheet.append(["DGX_001", 3, "action", "Enter project workspace", "click", "", "DGXLandingPage", "project_go_to_button", "element", "", "", "", "", "", "visible", 10, "N", "Y", "Go to project", ""])
    step_sheet.append(["DGX_001", 4, "assert", "Assert project workspace opened (placeholder)", "", "", "DGXLandingPage", "", "", "", "", "", "", "", "", 10, "N", "Y", "", PLACEHOLDER_REMARK])
    step_sheet.append(["DGX_001", 5, "action", "Open Set Boundaries panel", "click", "", "DGXBoundaryPage", "set_boundaries_button", "element", "", "", "", "", "", "visible", 10, "N", "Y", "Set Boundaries", ""])
    step_sheet.append(["DGX_001", 6, "assert", "Assert Set Boundaries panel opened (placeholder)", "", "", "DGXBoundaryPage", "", "", "", "", "", "", "", "", 10, "N", "Y", "", PLACEHOLDER_REMARK])
    step_sheet.append(["DGX_001", 7, "assert", "Verify upload entry is visible", "", "assert_text_contains", "DGXBoundaryPage", "upload_plot_button", "element", "", "", "UploadPlot CAD File", "string", "contains", "visible", 10, "N", "Y", "UploadPlot CAD File", ""])

    step_sheet.append(["DGX_002", 1, "action", "Open DGX demo landing page", "open_page", "", "DGXLandingPage", DGX_DEMO_ROUTE, "route", "", "", "", "", "", "dom_ready", 10, "N", "Y", "", ""])
    step_sheet.append(["DGX_002", 2, "action", "Open project card entry button", "click", "", "DGXLandingPage", "project_card_entry_button", "element", "", "", "", "", "", "visible", 10, "N", "Y", "Faya entry button", ""])
    step_sheet.append(["DGX_002", 3, "action", "Enter project workspace", "click", "", "DGXLandingPage", "project_go_to_button", "element", "", "", "", "", "", "visible", 10, "N", "Y", "Go to project", ""])
    step_sheet.append(["DGX_002", 4, "action", "Open Set Boundaries panel", "click", "", "DGXBoundaryPage", "set_boundaries_button", "element", "", "", "", "", "", "visible", 10, "N", "Y", "Set Boundaries", ""])
    step_sheet.append(["DGX_002", 5, "action", "Open plot upload dialog", "click", "", "DGXBoundaryPage", "upload_plot_button", "element", "", "", "", "", "", "visible", 10, "N", "Y", "UploadPlot CAD File", ""])
    step_sheet.append(["DGX_002", 6, "assert", "Assert upload dialog opened (placeholder)", "", "", "DGXBoundaryPage", "", "", "", "", "", "", "", "", 10, "N", "Y", "", PLACEHOLDER_REMARK])
    step_sheet.append(["DGX_002", 7, "action", "Open first layer selector", "click", "", "DGXBoundaryPage", "layer_select_button_1", "element", "", "", "", "", "", "visible", 10, "N", "Y", "First layer selector", ""])
    step_sheet.append(["DGX_002", 8, "action", "Choose Not Required for first layer", "click", "", "DGXBoundaryPage", "not_required_option", "element", "", "", "", "", "", "visible", 10, "N", "Y", "Not Required option", ""])
    step_sheet.append(["DGX_002", 9, "action", "Open second layer selector", "click", "", "DGXBoundaryPage", "layer_select_button_2", "element", "", "", "", "", "", "visible", 10, "N", "Y", "Second layer selector", ""])
    step_sheet.append(["DGX_002", 10, "action", "Choose Not Required for second layer", "click", "", "DGXBoundaryPage", "not_required_option", "element", "", "", "", "", "", "visible", 10, "N", "Y", "Not Required option", ""])
    step_sheet.append(["DGX_002", 11, "action", "Close upload dialog", "click", "", "DGXBoundaryPage", "cancel_button", "element", "", "", "", "", "", "visible", 10, "N", "Y", "Cancel button", ""])
    step_sheet.append(["DGX_002", 12, "action", "Go to next setup step", "click", "", "DGXBoundaryPage", "next_button", "element", "", "", "", "", "", "visible", 10, "N", "Y", "Next button", ""])
    step_sheet.append(["DGX_002", 13, "assert", "Assert layer visibility step opened (placeholder)", "", "", "DGXBoundaryPage", "", "", "", "", "", "", "", "", 10, "N", "Y", "", PLACEHOLDER_REMARK])
    step_sheet.append(["DGX_002", 14, "action", "Go to layer visibility step", "click", "", "DGXBoundaryPage", "next_button", "element", "", "", "", "", "", "visible", 10, "N", "Y", "Next button", ""])
    step_sheet.append(["DGX_002", 15, "action", "Hide all layers", "uncheck", "", "DGXBoundaryPage", "show_hide_all_checkbox", "element", "", "", "", "", "", "visible", 10, "N", "Y", "Show Hide All checkbox", ""])
    step_sheet.append(["DGX_002", 16, "action", "Enable first layer", "check", "", "DGXBoundaryPage", "layer_checkbox_1", "element", "", "", "", "", "", "visible", 10, "N", "Y", "First layer checkbox", ""])
    step_sheet.append(["DGX_002", 17, "action", "Enable second layer", "check", "", "DGXBoundaryPage", "layer_checkbox_2", "element", "", "", "", "", "", "visible", 10, "N", "Y", "Second layer checkbox", ""])
    step_sheet.append(["DGX_002", 18, "action", "Show all layers", "check", "", "DGXBoundaryPage", "show_hide_all_checkbox", "element", "", "", "", "", "", "visible", 10, "N", "Y", "Show Hide All checkbox", ""])
    step_sheet.append(["DGX_002", 19, "action", "Finish boundary setup", "click", "", "DGXBoundaryPage", "done_button", "element", "", "", "", "", "", "visible", 10, "N", "Y", "Done button", ""])
    step_sheet.append(["DGX_002", 20, "assert", "Assert design result area updated (placeholder)", "", "", "DGXBoundaryPage", "", "", "", "", "", "", "", "", 10, "N", "Y", "", PLACEHOLDER_REMARK])
    step_sheet.append(["DGX_002", 21, "assert", "Verify result project cell", "", "assert_text_contains", "DGXBoundaryPage", "project_result_cell", "element", "", "", "${project_result_name}", "string", "contains", "visible", 10, "N", "Y", "Project result cell", ""])

    data_sheet = workbook.create_sheet("Test_Data")
    data_sheet.append(["data_set_id", "data_name", "module", "env", "project_name", "project_result_name", "layer_option", "remark"])
    data_sheet.append(["DATA_DGX_DEFAULT_01", "DGX default demo data", "DGX", "demo", "Faya Al Saadiyat", "Park Hyatt Abu Dhabi Hotel", "Not Required", "Default data for the recorded DGX demo flow"])

    run_sheet = workbook.create_sheet("Run_Config")
    run_sheet.append(["config_key", "config_value", "remark"])
    run_sheet.append(["target_env", "demo", "Default target environment"])
    run_sheet.append(["browser", "chromium", "Default browser"])
    run_sheet.append(["include_tags", "dgx,demo", "Default tag filter"])
    run_sheet.append(["retry_failed_cases", "Y", "Retry failed cases"])

    dictionary_sheet = workbook.create_sheet("Dictionary")
    dictionary_sheet.append(["dict_type", "dict_value", "dict_label", "enabled", "remark"])
    for row in [
        ("priority", "P1", "High", "Y", ""),
        ("priority", "P2", "Medium", "Y", ""),
        ("test_level", "smoke", "Smoke", "Y", ""),
        ("status", "active", "Active", "Y", ""),
        ("action_key", "open_page", "Open page", "Y", ""),
        ("action_key", "click", "Click", "Y", ""),
        ("action_key", "check", "Check", "Y", ""),
        ("action_key", "uncheck", "Uncheck", "Y", ""),
        ("assert_key", "assert_text_contains", "Assert text contains", "Y", ""),
    ]:
        dictionary_sheet.append(list(row))

    return workbook


def _build_object_workbook() -> Workbook:
    workbook = Workbook()

    page_sheet = workbook.active
    page_sheet.title = "Page_Index"
    page_sheet.append([
        "page_name", "module", "sub_module", "route", "page_title", "load_wait_strategy",
        "load_timeout_sec", "frontend_hint", "api_group_hint", "status", "remark"
    ])
    page_sheet.append([
        "DGXLandingPage", "DGX", "Demo", DGX_DEMO_ROUTE, "DGX Design", "dom_ready", 10,
        "DGX demo landing page", "dgx", "active", "Default DGX entry page"
    ])
    page_sheet.append([
        "DGXBoundaryPage", "DGX", "Demo", DGX_DEMO_ROUTE, "DGX Design", "dom_ready", 10,
        "DGX boundary setup flow", "dgx", "active", "Boundary setup page state"
    ])

    object_sheet = workbook.create_sheet("Element_Objects")
    object_sheet.append([
        "object_key", "object_name", "page_name", "module", "sub_module", "object_type",
        "locator_primary_type", "locator_primary_value", "locator_backup_1_type", "locator_backup_1_value",
        "locator_backup_2_type", "locator_backup_2_value", "default_wait", "default_timeout_sec",
        "ai_component_hint", "frontend_file_hint", "api_hint", "enabled", "remark"
    ])
    object_rows = [
        ["project_card_entry_button", "Project card entry button", "DGXLandingPage", "DGX", "Demo", "button", "xpath", "(//button[normalize-space()='Faya Al Saadiyat'])[last()]", "text", "Faya Al Saadiyat", "", "", "visible", 10, "ProjectCard.EntryButton", "", "", "Y", "Recorded from codegen nth(1) click"],
        ["project_go_to_button", "Project go to button", "DGXLandingPage", "DGX", "Demo", "button", "xpath", "//button[contains(normalize-space(.), 'Faya Al Saadiyat') and contains(normalize-space(.), 'Go to')]", "text", "Faya Al Saadiyat Go to", "", "", "visible", 10, "ProjectCard.GoToButton", "", "", "Y", "Open the selected project"],
        ["set_boundaries_button", "Set Boundaries entry", "DGXBoundaryPage", "DGX", "Demo", "button", "text", "Set Boundaries", "partial_text", "Set Boundaries", "", "", "visible", 10, "BoundaryFlow.Entry", "", "", "Y", "Open the boundary workflow"],
        ["upload_plot_button", "Upload plot entry", "DGXBoundaryPage", "DGX", "Demo", "button", "text", "UploadPlot CAD File", "partial_text", "UploadPlot CAD File", "", "", "visible", 10, "BoundaryFlow.UploadPlot", "", "", "Y", "Open the CAD upload dialog"],
        ["layer_select_button_1", "First layer selector", "DGXBoundaryPage", "DGX", "Demo", "button", "xpath", "(//button[contains(normalize-space(.), '---- Select a Layer ----')])[1]", "partial_text", "---- Select a Layer ----", "", "", "visible", 10, "BoundaryFlow.LayerSelector1", "", "", "Y", "First visible layer selector"],
        ["layer_select_button_2", "Second layer selector", "DGXBoundaryPage", "DGX", "Demo", "button", "xpath", "(//button[contains(normalize-space(.), '---- Select a Layer ----')])[2]", "partial_text", "---- Select a Layer ----", "", "", "visible", 10, "BoundaryFlow.LayerSelector2", "", "", "Y", "Second visible layer selector"],
        ["not_required_option", "Not Required option", "DGXBoundaryPage", "DGX", "Demo", "option", "text", "Not Required", "partial_text", "Not Required", "", "", "visible", 10, "BoundaryFlow.NotRequired", "", "", "Y", "Shared option in the upload dialog"],
        ["cancel_button", "Cancel button", "DGXBoundaryPage", "DGX", "Demo", "button", "text", "Cancel", "partial_text", "Cancel", "", "", "visible", 10, "BoundaryFlow.Cancel", "", "", "Y", "Close the upload dialog"],
        ["next_button", "Next button", "DGXBoundaryPage", "DGX", "Demo", "button", "text", "Next", "partial_text", "Next", "", "", "visible", 10, "BoundaryFlow.Next", "", "", "Y", "Advance the left stepper flow"],
        ["show_hide_all_checkbox", "Show Hide All checkbox", "DGXBoundaryPage", "DGX", "Demo", "checkbox", "css", "div:has-text('Show/Hide All') input[type='checkbox']", "xpath", "//div[normalize-space()='Show/Hide All']/ancestor::div[1]//input[@type='checkbox']", "", "", "visible", 10, "BoundaryFlow.ShowHideAll", "", "", "Y", "Toggle all layers"],
        ["layer_checkbox_1", "First layer checkbox", "DGXBoundaryPage", "DGX", "Demo", "checkbox", "css", ".mkb-list-item > input", "xpath", "(//div[contains(@class, 'mkb-list-item')]//input[@type='checkbox'])[1]", "", "", "visible", 10, "BoundaryFlow.LayerCheckbox1", "", "", "Y", "Recorded first individual layer checkbox"],
        ["layer_checkbox_2", "Second layer checkbox", "DGXBoundaryPage", "DGX", "Demo", "checkbox", "css", ".mkb-list > div:nth-child(2) > input", "xpath", "(//div[contains(@class, 'mkb-list')]/*[2]//input[@type='checkbox'])[1]", "", "", "visible", 10, "BoundaryFlow.LayerCheckbox2", "", "", "Y", "Recorded second individual layer checkbox"],
        ["done_button", "Done button", "DGXBoundaryPage", "DGX", "Demo", "button", "text", "Done", "partial_text", "Done", "", "", "visible", 10, "BoundaryFlow.Done", "", "", "Y", "Finish layer configuration"],
        ["project_result_cell", "Project result cell", "DGXBoundaryPage", "DGX", "Demo", "cell", "text", "Park Hyatt Abu Dhabi Hotel", "partial_text", "Park Hyatt Abu Dhabi Hotel", "", "", "visible", 10, "BoundaryFlow.ResultCell", "", "", "Y", "Recorded result cell after boundary setup"],
    ]
    for row in object_rows:
        object_sheet.append(row)

    return workbook
