{
  description = "Mamba env for Erdos Institute data-science bootcam";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/25.05"; # When using the latest nixpkgs, mamba keeps segfaulting for some reason... Reverting to 25.05 seems to fix this. I should open an issue at some point unless someone has already done so.
    systems.url = "github:nix-systems/default";
    flake-utils = {
      url = "github:numtide/flake-utils";
      inputs.systems.follows = "systems";
    };
  };

  outputs = { nixpkgs, flake-utils, ... }: flake-utils.lib.eachDefaultSystem (system: let
    pkgs = import nixpkgs { inherit system; };

    # The following is gathered from information found in the micromamba section of <https://nixos.wiki/wiki/Python>, but with some modifications since that part of the wiki seems to be out-of-date.
    # The basic issue is that mamba really wants an FHS environment, especially with pip (perhaps without pip, we could get away without one, but idk).
    # Additionally, pip was having issues resolving dependencies, which seems to be fixed by adding `dash == 2.18.2` under the `pip` section of `environment.yaml`. Idk why this is necessary, but it works...
    bootcamp = pkgs.buildFHSEnv rec {
      name = "erdos_project";

      targetPkgs = ps: with ps; [

        # mamba
        mamba-cpp

        # mdbtools to convert microsoft access db into something that works with pandas
        mdbtools

        # vscode with some extensions
        (vscode-with-extensions.override {
          vscode = vscodium;
          vscodeExtensions = with vscode-extensions; [
            ms-toolsai.jupyter
            ms-python.python
            asvetliakov.vscode-neovim
          ];
        })

      ];

      profile = ''
        set -e

        PROJECT_ROOT="$(pwd)"

        export MAMBA_ROOT_PREFIX="$PROJECT_ROOT/.mamba"

        if ! [ -d "$MAMBA_ROOT_PREFIX" ]; then
          mamba create -n ${name}
          mamba install -y -n ${name} -f "$PROJECT_ROOT/environment.yml"
        fi

        eval "$(mamba shell hook --shell=posix)"

        mamba activate ${name}

        set +e
      '';
    };
  in {
    devShells.default = bootcamp.env;
  });
}
