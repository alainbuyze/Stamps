## Summary

During batch processing, the tutorial progress bar and image enhancement progress bar were overlapping on top of each other, making it difficult to track progress.

## Problem

The CLI (`cli.py`) and the image enhancer (`enhancer.py`) each created their own independent `Progress` instances from Rich. When `enhance_all_images()` was called from within the batch loop with `show_progress=True`, it created a nested Progress bar that overlapped with the outer batch progress bar.

## Solution

Share a single `Progress` instance between the CLI and the enhancer, allowing both progress bars to be displayed properly as separate tasks within the same Progress context.

### Changes Made

**`src/enhancer.py`:**
- Added optional `progress: Progress | None` parameter to `enhance_all_images()`
- When a shared Progress instance is provided, adds a subtask for image enhancement
- When running standalone (`show_progress=True` without shared progress), creates its own Progress context
- Subtask is automatically removed after enhancement completes

**`src/cli.py`:**
- Added `progress` parameter to `_generate_single()` function
- Updated batch processing loop to pass the Progress instance to `_generate_single()`
- Updated `enhance_all_images()` call to pass the shared progress instance

## Result

Progress bars now display stacked vertically:

```
⠋ [1/76] Case-01-Traffic-Light...      ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 1/76
⠋   Enhancing images...                 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 5/12
```

Both progress bars are visible and update independently. The image enhancement task is indented to indicate it's a subtask of the current tutorial being processed.

## Type

Improvement / UX Enhancement
