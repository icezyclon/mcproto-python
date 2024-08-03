#!/bin/bash
mkdir -p mcpb/_proto &&
mkdir -p proto &&
wget https://raw.githubusercontent.com/icezyclon/mcproto/main/src/main/proto/minecraft.proto -O proto/minecraft.proto && 
python -m grpc_tools.protoc --proto_path=proto --python_out=mcpb/_proto --grpc_python_out=mcpb/_proto proto/minecraft.proto
