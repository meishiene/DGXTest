# DGX Demo Recorded Cases

This document maps the recorded Playwright flow into the DGX demo test cases now used by the project templates.

## Source Recording

- Recorded URL: `https://dgx.xlook.ai/dgx/f2b850f5-14a0-4325-b56d-cb1213f63ec2`
- Raw codegen script: `templates/dgx_demo_codegen.py`
- Original capture: `outputs/recordings/dgx_demo_codegen.py`

## Promoted Test Cases

### DGX_001 Open DGX demo and reach Set Boundaries

1. Open the DGX demo landing page.
2. Click the `Faya Al Saadiyat` project entry button.
3. Click the `Go to` button for that project.
4. Click `Set Boundaries`.
5. Assert the `UploadPlot CAD File` entry is visible.

### DGX_002 Configure boundary layers and finish setup

1. Open the DGX demo landing page.
2. Enter the `Faya Al Saadiyat` project.
3. Open `Set Boundaries`.
4. Open the `UploadPlot CAD File` dialog.
5. Open the first visible layer selector and choose `Not Required`.
6. Open the second visible layer selector and choose `Not Required`.
7. Close the dialog with `Cancel`.
8. Click `Next` twice.
9. Uncheck `Show/Hide All`.
10. Check the first two visible layer checkboxes.
11. Check `Show/Hide All` again.
12. Click `Done`.
13. Assert the result cell contains `Park Hyatt Abu Dhabi Hotel`.

## Notes

- The raw recording also contains extra exploratory clicks after `Done`, including the result cell, an SVG click, and direct stepper jumps.
- Those trailing actions were intentionally kept out of the default Excel suite because the generated locators are more brittle than the boundary flow locators.
- If we want to automate those later, we should inspect the live DOM and promote them with more stable object keys first.
