#!/bin/bash
mkdir -p mcproto/mcpb &&
mkdir -p proto &&
wget https://raw.githubusercontent.com/icezyclon/mcproto/main/src/main/proto/minecraft.proto -O proto/minecraft.proto && 
python -m grpc_tools.protoc --proto_path=proto --python_out=mcproto/mcpb --grpc_python_out=mcproto/mcpb proto/minecraft.proto
