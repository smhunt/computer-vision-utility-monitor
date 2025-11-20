# TODO: Dynamic Snapshot Card Reload

## Objective
After clicking "Reprocess" or "Capture", reload the snapshot cards dynamically without a full page refresh.

## Current Behavior
- Reprocess button: Shows "✅ Done!" but requires manual F5 to see updated reading
- Capture button: Re-enables after 2 seconds but doesn't show new snapshot without F5

## Desired Behavior
- After reprocess/capture completes, automatically reload just the snapshot grid
- No page flash, no scroll position loss
- Smooth update with new/updated snapshot cards

## Implementation Approach

### 1. Create API Endpoint for Snapshot Data
```python
@app.route('/api/snapshots/<meter_name>')
def api_get_snapshots(meter_name):
    """Return snapshot list as JSON"""
    snapshots = []
    snapshot_dir = LOG_DIR / "meter_snapshots" / meter_name
    # ... load snapshots ...
    return jsonify({'snapshots': snapshots})
```

### 2. Add JavaScript Function to Reload Snapshots
```javascript
async function reloadSnapshots() {
    const response = await fetch('/api/snapshots/{{ meter_name }}');
    const data = await response.json();

    // Update DOM with new snapshot cards
    const container = document.getElementById('snapshots-grid');
    container.innerHTML = renderSnapshots(data.snapshots);
}

function renderSnapshots(snapshots) {
    // Generate HTML for snapshot cards
    return snapshots.map(snapshot => `
        <div class="snapshot-card">
            <!-- snapshot HTML -->
        </div>
    `).join('');
}
```

### 3. Update Reprocess/Capture Success Handlers
```javascript
// After reprocess success
if (data.status === 'success') {
    btn.textContent = '✅ Done!';
    btn.style.background = '#28a745';

    // Reload snapshot cards
    await reloadSnapshots();
}

// After capture success
if (data.status === 'success') {
    // ... show success message ...

    // Wait a moment, then reload
    setTimeout(() => {
        reloadSnapshots();
    }, 1000);
}
```

### 4. Considerations

**Template vs JavaScript Rendering:**
- Option A: Return full HTML from backend, update via `innerHTML`
- Option B: Return JSON data, render with JavaScript template
- Recommend: Option B for cleaner separation

**Preserve State:**
- Keep scroll position
- Maintain expanded modals if open
- Don't reload if user is interacting with card

**Loading Indicator:**
- Show subtle loading state while fetching
- Fade in new cards smoothly

**Error Handling:**
- If reload fails, show retry button
- Don't break existing cards

## Files to Modify

1. **meter_preview_ui.py** - Add `/api/snapshots/<meter_name>` endpoint
2. **templates/meter.html** - Add JavaScript reload functions
3. Test with both reprocess and capture workflows

## Sub-Agent Prompt

```
Implement dynamic snapshot card reloading without page refresh.

Requirements:
1. Add API endpoint `/api/snapshots/<meter_name>` that returns snapshot data as JSON
2. Add JavaScript function `reloadSnapshots()` that fetches and updates the snapshot grid
3. Call `reloadSnapshots()` after reprocess/capture success
4. Preserve scroll position and don't disrupt user interaction
5. Show subtle loading indicator during reload
6. Handle errors gracefully

Files to modify:
- meter_preview_ui.py (add API endpoint)
- templates/meter.html (add reload JavaScript)

Current snapshot loading is in the `meter_detail()` function at line ~160.
Snapshot cards are rendered in the template around line ~340.
```

## Success Criteria

- ✅ Click reprocess → See updated reading appear without F5
- ✅ Click capture → New snapshot appears at top without F5
- ✅ No page flash or scroll jump
- ✅ Works smoothly even with multiple rapid clicks
- ✅ Error states handled (network failure, timeout, etc.)
