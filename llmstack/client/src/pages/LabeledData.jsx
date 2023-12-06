import React, { useEffect, useState } from "react";
import Box from "@mui/material/Box";
import TextField from "@mui/material/TextField";
import Chip from "@mui/material/Chip";
import Button from "@mui/material/Button";
import Stack from "@mui/material/Stack";
import Collapse from "@mui/material/Collapse";
import IconButton from "@mui/material/IconButton";
import Table from "@mui/material/Table";
import TableBody from "@mui/material/TableBody";
import TableCell from "@mui/material/TableCell";
import TableContainer from "@mui/material/TableContainer";
import TableHead from "@mui/material/TableHead";
import TableRow from "@mui/material/TableRow";
import Typography from "@mui/material/Typography";
import Paper from "@mui/material/Paper";
import KeyboardArrowDownIcon from "@mui/icons-material/KeyboardArrowDown";
import KeyboardArrowUpIcon from "@mui/icons-material/KeyboardArrowUp";
import { axios } from "../data/axios";
import MuiAlert from "@mui/material/Alert";
import Snackbar from "@mui/material/Snackbar";

import TextAnnotator from "../components/TextAnotater";
import TextSelector from "text-selection-react";
import { TAGS } from "../components/datasource/DataSourceEntryContent";
import { TAG_COLORS } from "../components/datasource/DataSourceEntryContent";
import { DeleteOutlined } from "@mui/icons-material";
import DeleteConfirmationModal from "../components/DeleteConfirmationModal";
export default function LabeledData() {
  const [rows, setRows] = React.useState([]);
  useEffect(() => {
    axios()
      .get(`/api/datasource_labels`)
      .then((response) => {
        console.log(response.data);
        setRows(response.data);
      });
  }, []);
  return (
    <div>
      <h1>Labeled Data</h1>
      {rows.length > 0 && <CollapsibleTable rows={rows} />}
    </div>
  );
}
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

function Row(props) {
  const { row } = props;
  const [isDeleteConfirmationModalOpen, setDeleteConfirmationModalOpen] =
    useState(false);
  const [isToastOpen, showToast] = useState(false);
  const [successToast, setSuccessToast] = useState(false);
  const [isLabelingMode, setIsLabelingMode] = useState(false);
  const [open, setOpen] = useState(false);
  const [data, setData] = useState();
  const [annotations, setAnnotation] = useState(row.labels);
  const [name, setName] = useState(row.labels_name);
  const [vars, setVars] = useState([{ key: "", value: "", description: "" }]);
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
    if (open) {
      axios()
        .get(`api/datasource_labels/${row.uuid}/text_content`)
        .then((response) => {
          console.log(response.data);
          setData(response.data.content);
          // setRows(response.data);
        });
    }
    if (row.variables && row.variables.length > 0) {
      setVars(row.variables);
    } else {
      setVars([]);
    }
  }, [open]);

  const onSave = () => {
    console.log({ name, annotations, row });

    if (annotations.length === 0) {
      console.log("No annotations");
      setDeleteConfirmationModalOpen(true);
      return;
    }

    const validVars = vars.filter(
      (v) =>
        v.key.trim() !== "" &&
        v.value.trim() !== "" &&
        v.description.trim() !== "",
    );

    if (validVars.length !== vars.length) {
      console.log("Invalid variables");
      showToast(true);
      return;
    }

    axios()
      .put(`api/datasource_labels/${row.uuid}`, {
        name,
        labels: annotations,
        data_source: row.data_source,
        user_id: 1,
        variables: validVars,
      })
      .then((response) => {
        console.log(response.data.variables);
        setAnnotation(response.data.labels);
        setName(response.data.labels_name);
        setVars(response.data.variables);
        setSuccessToast(true);
      })
      .finally(() => {
        setIsLabelingMode(false);
      });
  };
  const handleClose = (event, reason) => {
    if (reason === "clickaway") {
      return;
    }
    showToast(false);
  };
  const onDelete = (id) => {
    axios()
      .delete(`api/datasource_labels/${id}`)
      .then((response) => {
        console.log(response);
        window.location.reload();
      })
      .finally(() => {
        setDeleteConfirmationModalOpen(false);
      });
  };

  return (
    <React.Fragment>
      <Snackbar
        open={isToastOpen}
        autoHideDuration={3000}
        onClose={handleClose}
      >
        <MuiAlert onClose={handleClose} severity="error" sx={{ width: "100%" }}>
          All fields for variables must be filled out
        </MuiAlert>
      </Snackbar>
      <Snackbar
        open={successToast}
        autoHideDuration={3000}
        onClose={handleClose}
      >
        <MuiAlert
          onClose={(event, reason) => {
            if (reason === "clickaway") {
              return;
            }
            setSuccessToast(false);
          }}
          severity="success"
          sx={{ width: "100%" }}
        >
          Successfully saved
        </MuiAlert>
      </Snackbar>
      <TableRow
        hover
        onClick={() => setOpen(!open)}
        sx={{ "& > *": { borderBottom: "unset" }, cursor: "pointer" }}
      >
        <TableCell>
          <IconButton
            aria-label="expand row"
            size="small"
            onClick={() => setOpen(!open)}
          >
            {open ? <KeyboardArrowUpIcon /> : <KeyboardArrowDownIcon />}
          </IconButton>
        </TableCell>
        <TableCell>{name}</TableCell>
        <TableCell>{row.data_source_name}</TableCell>
        <TableCell>{row.created_at}</TableCell>
        <TableCell>{row.updated_at}</TableCell>
        <TableCell>me</TableCell>
      </TableRow>
      <TableRow>
        <TableCell style={{ paddingBottom: 0, paddingTop: 0 }} colSpan={6}>
          <Collapse in={open} timeout="auto" unmountOnExit>
            {data && (
              <Box sx={{ margin: 1 }}>
                <DeleteConfirmationModal
                  id={row.uuid}
                  title="Delete Data Source Entry"
                  text={
                    <div>
                      Are you sure you want to delete{" "}
                      <span style={{ fontWeight: "bold" }}>
                        {row.labels_name}
                      </span>{" "}
                      ?
                    </div>
                  }
                  open={isDeleteConfirmationModalOpen}
                  onOk={onDelete}
                  onCancel={() => {
                    setDeleteConfirmationModalOpen(false);
                  }}
                />
                <Stack direction="row" sx={{ mb: "12px", mt: "12px" }}>
                  {isLabelingMode ? (
                    <TextField
                      type="text"
                      label="Label Group Name"
                      sx={{ width: "400px" }}
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                    />
                  ) : (
                    <Typography variant="h6" gutterBottom component="div">
                      {name}
                    </Typography>
                  )}
                  {!isLabelingMode && (
                    <Stack direction="row" gap={1}>
                      <Button
                        variant="contained"
                        sx={{ ml: "10px" }}
                        onClick={() => {
                          setIsLabelingMode(true);
                          if (row.variables && row.variables.length > 0) {
                            setVars(row.variables);
                          } else {
                            setVars([
                              {
                                key: "",
                                value: "",
                                description: "",
                              },
                            ]);
                          }
                        }}
                      >
                        Edit
                      </Button>
                      <Button
                        variant="contained"
                        color="error"
                        sx={{ ml: "10px" }}
                        onClick={() => {
                          setDeleteConfirmationModalOpen(true);
                        }}
                      >
                        Delete
                      </Button>
                    </Stack>
                  )}
                </Stack>
                <h2>Variables</h2>
                {isLabelingMode ? (
                  <>
                    <Box sx={{ mb: "10px" }}>
                      {vars.map((v, index) => (
                        <Stack
                          direction={"row"}
                          gap={1}
                          sx={{ mb: "10px" }}
                          key={v}
                        >
                          <TextField
                            label="Key"
                            value={v.key}
                            type="text"
                            onChange={(e) => {
                              const newVars = [...vars];
                              newVars[index].key = e.target.value;
                              setVars(newVars);
                            }}
                          />
                          <TextField
                            label="Value"
                            value={v.value}
                            type="text"
                            onChange={(e) => {
                              const newVars = [...vars];
                              newVars[index].value = e.target.value;
                              setVars(newVars);
                            }}
                          />
                          <TextField
                            label="Description"
                            value={v.description}
                            type="text"
                            onChange={(e) => {
                              const newVars = [...vars];
                              newVars[index].description = e.target.value;
                              setVars(newVars);
                            }}
                          />
                          {index > 0 && (
                            <IconButton
                              onClick={() => {
                                const newVars = [...vars];
                                newVars.splice(index, 1);
                                setVars(newVars);
                              }}
                            >
                              <DeleteOutlined />
                            </IconButton>
                          )}
                        </Stack>
                      ))}
                      <Button
                        variant="contained"
                        onClick={() => {
                          setVars([
                            ...vars,
                            {
                              key: "",
                              value: "",
                            },
                          ]);
                        }}
                      >
                        Add Variable
                      </Button>
                    </Box>
                  </>
                ) : (
                  <>
                    <Stack gap={1} sx={{ mb: "10px" }}>
                      {vars.map((v) => (
                        <Box>
                          <h3 key={v.key}>
                            <Chip label={v.key} /> : {v.value}
                          </h3>
                          <p>Description: {v.description}</p>
                        </Box>
                      ))}
                    </Stack>
                  </>
                )}

                {isLabelingMode && (
                  <Stack
                    sx={{
                      mt: "50px",
                      mb: "10px",
                      width: "620px",
                      justifyContent: "flex-end",
                    }}
                    direction="row"
                  >
                    <Button
                      variant="secondary"
                      sx={{ ml: "10px" }}
                      onClick={() => {
                        setIsLabelingMode(false);
                        setAnnotation(row.labels);
                        setName(row.labels_name);
                        if (row.variables && row.variables.length > 0) {
                          setVars(row.variables);
                        } else {
                          setVars([]);
                        }
                      }}
                    >
                      Cancel
                    </Button>
                    <Button
                      variant="contained"
                      onClick={onSave}
                      color="success"
                    >
                      Save Changes
                    </Button>
                  </Stack>
                )}

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
                {annotations && (
                  <TextAnnotator
                    style={{
                      maxWidth: 500,
                      lineHeight: 1.5,
                      whiteSpace: "pre-line",
                    }}
                    content={data}
                    value={annotations}
                    onChange={(value) => {
                      if (isLabelingMode) {
                        setAnnotation(
                          annotations.filter((a) => a.localId !== value),
                        );
                      }
                    }}
                  />
                )}
                {data && isLabelingMode && (
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
                )}
              </Box>
            )}
          </Collapse>
        </TableCell>
      </TableRow>
    </React.Fragment>
  );
}

function CollapsibleTable({ rows }) {
  return (
    <TableContainer component={Paper}>
      <Table aria-label="collapsible table">
        <TableHead>
          <TableRow>
            <TableCell />
            <TableCell>Label Group Name</TableCell>
            <TableCell>Data Source</TableCell>
            <TableCell>Created At</TableCell>
            <TableCell>Updated At</TableCell>
            <TableCell>Owner</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {rows.map((row) => (
            <Row key={row.data_source_name} row={row} />
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
}
