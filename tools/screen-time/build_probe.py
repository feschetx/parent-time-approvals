"""Build a local-only Apple Screen Time probe. No credentials or uploads."""
import json
import plistlib
import sys
import uuid
from pathlib import Path


def uid():
    return str(uuid.uuid4()).upper()


def token(value):
    return {"Value": value, "WFSerializationType": "WFTextTokenAttachment"}


def output(ident, name):
    return token({"OutputUUID": ident, "Type": "ActionOutput", "OutputName": name})


def text(string, attachments):
    return {"Value": {"string": string, "attachmentsByRange": attachments},
            "WFSerializationType": "WFTextTokenString"}


def build():
    activity, repeat, row, report = uid(), uid(), uid(), uid()
    duration = {"VariableName": "Repeat Item", "Type": "Variable", "Aggrandizements": [
        {"PropertyUserInfo": {"WFLinkEntityContentPropertyUserInfoPropertyIdentifier": "totalDuration"},
         "Type": "WFPropertyVariableAggrandizement", "PropertyName": "totalDuration"},
        {"WFUnitSymbol": "s", "WFMeasurementUnitType": "Duration", "Type": "WFUnitVariableAggrandizement"}]}
    actions = []
    def add(name, **params):
        actions.append({"WFWorkflowActionIdentifier": name, "WFWorkflowActionParameters": params})
    add("is.workflow.actions.comment", WFCommentActionText=
        "Local-only setup test. Choose this iPhone when importing. Reads today's app activity; "
        "copies and displays app names and source durations. No uploads, messages, browsing URLs, "
        "account changes, blocking or limits. An empty result means data unavailable, not zero use.")
    add("com.apple.intelligenceplatform.IntelligencePlatform.IntelligencePlatformDataActionsAppIntentsExtension.CalculateAppUsageIntent",
        UUID=activity, activityType="apps")
    add("is.workflow.actions.repeat.each", WFInput=output(activity, "Activity"), GroupingIdentifier=repeat, WFControlFlowMode=0)
    add("is.workflow.actions.gettext", UUID=row, WFTextActionText=text("\ufffc\t\ufffc", {
        "{0, 1}": {"VariableName": "Repeat Item", "Type": "Variable"}, "{2, 1}": duration}))
    add("is.workflow.actions.repeat.each", UUID=repeat, GroupingIdentifier=repeat, WFControlFlowMode=2)
    add("is.workflow.actions.gettext", UUID=report, WFTextActionText=text(
        "SCREEN TIME SETUP TEST v1\nPeriod: Today (phone calendar/time zone)\n"
        "Scope: device chosen during setup; verify it is this iPhone\n"
        "Source: Apple Screen Time; not independently verified attention\n"
        "App\tSource duration (seconds)\n\ufffc\n"
        "END - Empty rows are unavailable data, not a zero-use finding.",
        {"{252, 1}": {"OutputUUID": repeat, "Type": "ActionOutput", "OutputName": "Repeat Results"}}))
    # Compute attachment position rather than relying on a literal offset.
    params = actions[-1]["WFWorkflowActionParameters"]["WFTextActionText"]["Value"]
    attachment = next(iter(params["attachmentsByRange"].values()))
    params["attachmentsByRange"] = {"{%d, 1}" % params["string"].index("\ufffc"): attachment}
    add("is.workflow.actions.setclipboard", WFInput=output(report, "Text"), WFLocalOnly=True)
    # Show Result is a text field, not a content-item field. A bare token
    # attachment imports as an unbound "Content" placeholder on iOS 27.
    add("is.workflow.actions.showresult", Text=text("\ufffc", {
        "{0, 1}": {"OutputUUID": report, "Type": "ActionOutput", "OutputName": "Text"}}))
    workflow = {
        "WFWorkflowName": "Screen Time Setup Check", "WFWorkflowClientVersion": "4046.0.2.2",
        "WFWorkflowMinimumClientVersion": 900, "WFWorkflowMinimumClientVersionString": "900",
        "WFWorkflowIcon": {"WFWorkflowIconStartColor": 463140863, "WFWorkflowIconGlyphNumber": 61440},
        "WFWorkflowActions": actions, "WFWorkflowTypes": [], "WFWorkflowInputContentItemClasses": [],
        "WFWorkflowOutputContentItemClasses": ["WFStringContentItem"],
        "WFWorkflowImportQuestions": [{"ActionIndex": 1, "Category": "Parameter", "ParameterKey": "selectedDevice",
            "Text": "Choose THIS iPhone (not All Devices). This setup check reads only the chosen device.", "DefaultValue": ""}],
        "WFWorkflowHasShortcutInputVariables": False,
    }
    assert len(actions) == 8
    assert all("url" not in a["WFWorkflowActionIdentifier"] for a in actions)
    return workflow


if __name__ == "__main__":
    dest = Path(sys.argv[1] if len(sys.argv) > 1 else "build")
    dest.mkdir(parents=True, exist_ok=True)
    workflow = build()
    raw = plistlib.dumps(workflow, fmt=plistlib.FMT_BINARY)
    assert plistlib.loads(raw) == workflow
    (dest / "Screen-Time-Setup-Check.unsigned.shortcut").write_bytes(raw)
    (dest / "Screen-Time-Setup-Check.review.json").write_text(json.dumps(workflow, indent=2), encoding="utf-8")
    print("Built local-only Screen Time setup probe; no credentials, endpoints or uploads.")
