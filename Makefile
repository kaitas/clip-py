SHELL := /bin/bash
VERSION := 1.2.0
REVISION := $(shell git rev-parse --short HEAD)

# Detect Go Modules
USE_MODULES := $(wildcard go.mod)

# Show version
version:
	@echo "Version: $(VERSION)($(REVISION))"

# Legacy Glide path (used only if no go.mod)
glide:
ifeq ($(shell which glide 2>/dev/null),)
	mkdir -p $(GOPATH)/bin
	curl -s https://glide.sh/get | sh
endif

deps:
ifeq ($(USE_MODULES),)
	# Glide (legacy)
	@if [ -z "$$(find . -depth 1 -name vendor 2>/dev/null)" ]; then glide install; fi
else
	# Go Modules
	go mod tidy
endif

test: deps
ifeq ($(USE_MODULES),)
	go test -v
else
	go test -v ./...
endif

build: deps
ifeq ($(USE_MODULES),)
	go build -o clip
else
	go build -o clip ./...
endif
