import React from "react";

import Mark from "./Mark";
import {
  selectionIsEmpty,
  selectionIsBackwards,
  splitWithOffsets,
} from "./utils";

const Split = (props) => {
  if (props.mark) return <Mark {...props} />;

  return (
    <span
      data-start={props.start}
      data-end={props.end}
      onClick={() => props.onClick({ start: props.start, end: props.end })}
    >
      {props.content}
    </span>
  );
};

const TextAnnotator = (props) => {
  const handleSplitClick = ({ start, end }) => {
    props.onChange(`${start}-${end}`);
  };

  const { content, value, style } = props;
  const splits = splitWithOffsets(content, value);
  return (
    <pre style={style}>
      {splits.map((split) => (
        <Split
          key={`${split.start}-${split.end}`}
          {...split}
          onClick={handleSplitClick}
        />
      ))}
    </pre>
  );
};

export default TextAnnotator;
