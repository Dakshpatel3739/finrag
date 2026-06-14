Form primitives — `Field` wraps any control with label/hint/error; `Input`, `Textarea`, `Select`, `Checkbox`, `Switch` are the controls.

```jsx
<Field label="Workspace name" required hint="Visible to your team">
  <Input placeholder="e.g. Acme Treasury" />
</Field>
<Field label="Access role">
  <Select defaultValue="finance">
    <option value="owner">Owner</option>
    <option value="finance">Finance</option>
    <option value="hr">HR</option>
    <option value="employee">Employee</option>
  </Select>
</Field>
<Checkbox checked label="Only show grounded answers" onChange={fn} />
<Switch checked label="Redact restricted chunks" onChange={fn} />
```

All controls are controlled where applicable. `Input` accepts `icon`, `invalid`, `mono` (for ids/figures) and `size`. Use `Field`'s `error` prop to switch a control to the invalid state with a message.
