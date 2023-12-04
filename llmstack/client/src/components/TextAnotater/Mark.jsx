import React from "react";

const Mark = (props) => (
  <mark
    style={{
      backgroundColor: props.color || "#84d2ff",
      padding: "0 4px",
      borderRadius: "4px",
    }}
    data-start={props.start}
    data-end={props.end}
    onClick={() => props.onClick({ start: props.start, end: props.end })}
  >
    {props.content}
    {props.tag && (
      <span style={{ fontSize: "0.8em", fontWeight: 500, marginLeft: 6 }}>
        {props.tag}
      </span>
    )}
  </mark>
);

export default Mark;
