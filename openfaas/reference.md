# Supported Labels Reference

This document references the labels one can apply to OpenFaas functions to better control their integration in XC Scenario.

All labels are prefixed with `xcomponent.com.`.

| <b>Label</b> | <b>Meaning</b> |
| :---------- | :---- |
| `label` | List of labels to apply to this function. Separators: `/`, `\|` and `-` |
| `inputs.X` | Declares an input parameter named `X`, All the XC Scenario base types can be used : String, Number, Boolean. |
| `outputs.X` | Declares an output parameter named `X`, All the XC Scenario base types can be used : String, Number, Boolean. |
| `allowedWorkspaces | List of workspaces where this function can run. Separator: `;` |
