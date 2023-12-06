import React, { useEffect, useState } from "react";
import {
  Box,
  Button,
  Chip,
  CircularProgress,
  Divider,
  Drawer,
  Stack,
  TextField,
} from "@mui/material";

import { axios } from "../../data/axios";
import TextSelector from "text-selection-react";
import TextAnnotator from "../TextAnotater";
export const TAGS = ["GUIDE", "TROUBLESHOOTING", "GENERAL"];
export const TAG_COLORS = {
  GUIDE: "#dce391",
  TROUBLESHOOTING: "#84d2ff",
  GENERAL: "#72c669",
};
function findSubstringIndexes(mainString, substring) {
  const startIndex = mainString.indexOf(substring);

  if (startIndex !== -1) {
    const endIndex = startIndex + substring.length - 1;
    return { start: startIndex, end: endIndex };
  } else {
    // Return some indication that the substring is not found
    return { start: -1, end: -1 };
  }
}
function DataSourceEntryContent({ onCancel, dataSourceEntry, open }) {
  const [data, setData] = useState(null);
  const [metadata, setMetadata] = useState(null);
  const [loading, setLoading] = useState(false);
  const [name, setName] = useState(`label-${Date.now()}`);
  const [annotations, setAnnotation] = useState([
    // { localId: "0-19", start: 0, end: 19, tag: "GUIDE", color: "#dce391" },
  ]);

  const selectionHandler = ({ text, tag, content }) => {
    const { start, end } = findSubstringIndexes(content, text);
    setAnnotation([
      ...annotations,
      {
        start,
        end,
        tag,
        color: TAG_COLORS[tag],
        localId: `${start}-${end}`,
      },
    ]);
  };
  useEffect(() => {
    if (dataSourceEntry?.config?.document_ids) {
      axios()
        .get(`/api/datasource_entries/${dataSourceEntry.uuid}/text_content`)
        .then((response) => {
          setData(response.data?.content);
          setMetadata(response.data?.metadata);
        })
        .finally(() => setLoading(false));
    } else {
      setData(null);
    }
  }, [dataSourceEntry]);

  const onSave = () => {
    console.log({ name, annotations, dataSourceEntry });
    setLoading(true);
    axios()
      .post(`api/datasource_labels`, {
        name,
        labels: annotations,
        data_source: dataSourceEntry.datasource.uuid,
        // user_id: dataSourceEntry.datasource.owner.id,
        user_id: 1,
      })
      .then((response) => {
        console.log(response);
        window.location.reload();
      })
      .finally(() => setLoading(false));
  };

  return (
    <Drawer
      open={open}
      onClose={onCancel}
      anchor="right"
      sx={{ "& .MuiDrawer-paper": { maxWidth: "50%" }, maxWidth: "50%" }}
    >
      <Box>
        <Stack direction={"row"} gap={1} sx={{ mb: "10px", mt: "10px" }}>
          <Button onClick={() => onCancel()} sx={{ alignSelf: "left" }}>
            X
          </Button>
          {Object.keys(metadata || {}).map((key) => (
            <Chip
              label={`${key}: ${metadata[key]}`}
              size="small"
              key={key}
              sx={{ borderRadius: "10px", marginTop: "5px" }}
            />
          ))}
        </Stack>

        {annotations.length > 0 && (
          <Stack
            direction={"row"}
            gap={1}
            sx={{ mb: "10px", mt: "10px", ml: "10px" }}
          >
            <TextField
              value={name}
              onChange={(e) => setName(e.target.value)}
              id="standard-basic"
              label="Name"
              variant="standard"
              sx={{
                minWidth: "400px",
              }}
            />
            <Button onClick={onSave} sx={{ alignSelf: "left" }}>
              Save Labels
            </Button>
          </Stack>
        )}

        <Divider />
        {loading ? (
          <CircularProgress />
        ) : (
          <div style={{ margin: "0px 10px" }}>
            <Stack direction="row" gap={2}>
              {Object.keys(TAG_COLORS).map((tag) => (
                <Chip
                  label={tag}
                  size="small"
                  key={tag}
                  sx={{
                    borderRadius: "10px",
                    marginTop: "5px",
                    backgroundColor: TAG_COLORS[tag],
                  }}
                />
              ))}
            </Stack>
            {data && (
              <>
                <TextSelector
                  events={TAGS.map((tag) => ({
                    text: tag,
                    handler: (text) => {
                      selectionHandler({
                        text: text.textContent,
                        tag,
                        content: data,
                      });
                    },
                  }))}
                  colorText={false}
                />
                <TextAnnotator
                  style={{
                    maxWidth: 500,
                    lineHeight: 1.5,
                    whiteSpace: "pre-line",
                  }}
                  content={data}
                  value={annotations}
                  onChange={(value) => {
                    setAnnotation(
                      annotations.filter((a) => a.localId !== value),
                    );
                  }}
                  // getSpan={(span) => ({
                  //   ...span,
                  //   tag: currentTag,
                  //   color: TAG_COLORS[currentTag],
                  // })}
                />
              </>
            )}
          </div>
        )}
      </Box>
    </Drawer>
  );
}

export default DataSourceEntryContent;
