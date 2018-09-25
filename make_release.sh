#!/bin/bash

##-Variables-##
args=$#
args_left=$args
to_vers=""
proj_root=$(dirname "$0")
pkgname=$(cat ${proj_root}/debian/control | grep '^Source: ' | sed 's/^Source: //')
skip_tag="false"
skip_commit="false"
skip_version_update="false"
skip_changelog_update="false"
output_changelog="false"
version_files=()

##-Funcrions-##
function deb_gen_commit_range {
    new_vers="$1"
    first_commit=$(git rev-list --max-parents=0 HEAD)
    last_commit=$(git rev-parse HEAD)
    prev_tag="$first_commit"
    version_tags=( $(git tag -l 'v*' | sort -V) )
    for t in "${version_tags[@]}" ; do
        echo "$prev_tag..$t"
        prev_tag="$t"
    done
    echo "${prev_tag}..${last_commit}_${new_vers}"
}

function deb_gen_changelog {
    new_vers="$1"
    for r in $(deb_gen_commit_range "$new_vers" | tac) ; do
        r_split=( ${r//_/ } )
        range=${r_split[0]}
        nvers=${r_split[1]}
        range_split=( ${range//../ } )
        tag=${range_split[1]}
        vers=${nvers:-$tag}
        vers=${vers#v}
        (
            echo -e "\n$pkgname (${vers}) unstable; urgency=low\n"
            git log --pretty=format:'%s%n%b%n  - Authored by: %an <%ae>%n' ${range} | sed '/^Merge branch.*/,/^ \+- Authored by:.*/d ; /^$/d ; s/^/  /'
            echo
            git log --pretty=format:'%s%n -- %an <%ae>  %aD %n%n' ${range} | sed '/^Merge branch.*/,/^ \+-- .*/d ; /^$/d ; /^[^ ]/d' | head -n 1
        )
    done | sed '1d;s/^ +$//'
}

function check_tag {
    check_tag="$1"
    for tag in $(git tag -l 'v*' | sort -V) ; do
        if [ "$check_tag" == "$tag" ] ; then
            return 1
        fi
    done
    return 0
}

function sync_upstream_tags {
    local remote
    if [ -z "$1" ] ; then
        remote='origin'
        if git remote | grep -q upstream ; then
            remote='upstream'
        fi
    else
        remote="$1"
    fi
    git fetch --tags $remote
}

function help {
cat <<EOF
----------------------------------------
Usage: $(basename $0) <options>

Options:
    --version,-v <version>  New version number to use for creating tags and generating
                            the debian changelog
    --skip-commit           Skip commiting the changes
    --skip-tag              Skip creating the tag
    --skip-version-update   Skip updating the version in files
    --skip-changelog-update Skip Updating changelog
    --only-output-changelog Only generate and output the changelog
    --help                  Display this help

EOF
}

##-Main-##
while [ $args_left -ge 1 ] ; do
    case "$1" in
        --version|-v)
            if [ ! -z "$2" ] ; then
                to_vers="$2"
                shift
                let args_left=args_left-1
            fi
            ;;
        --skip-commit|-C)
            skip_commit="true"
            ;;
        --skip-tag|-T)
            skip_tag="true"
            ;;
        --skip-version-update|-r)
            skip_version_update="true"
            ;;
        --skip-changelog-update|-c)
            skip_changelog_update="true"
            ;;
        --only-output-changelog|-o)
            output_changelog="true"
            ;;
        --help|-h)
            help
            exit 0
            ;;
        *)
            echo "Unknown argument: $1"
            exit 1
    esac
    shift
    let args_left=args_left-1
done

#Arg checking
if [ -z "$to_vers" ] ; then
    echo "A version number must be supplied with --version, or from environment variable: VERSION"
    exit 1
fi

if [[ "$to_ver" =~ ^v.* ]] ; then
    echo "Version number should not be pre-fixes with a 'v'"
    exit 1
fi

if [ -f "${proj_root}/.make_releaserc" ] ; then
    source "${proj_root}/.make_releaserc"
fi

#Make sure that our tags are insync
sync_upstream_tags "$remote_name"

#Check that the version doesn't already have a tag.
if ! check_tag v${to_vers}; then
    echo "Tag: v${to_vers} already exists, aborting"
    exit 1
fi

if [ "$output_changelog" == "true" ] ; then
    deb_gen_changelog $to_vers
    exit 0
fi

if [ "$skip_version_update" == "false" ] ; then
    #Update version in files
    for file in "${version_files[@]}"; do
        echo "Updating version string in: ${file}"
        sed -i "s/^__version__ *= *.\+/__version__ = '${to_vers}'/" ${proj_root}/${file}
    done

    #Update setup.py
    echo "Updating setup.py"
    sed -i "s/version=.\+/version='${to_vers}',/" ${proj_root}/setup.py
fi

if [ "$skip_changelog_update" == "false" ] ; then
    #Update debian changelog
    echo "Re-generating debian/changelog"
    deb_gen_changelog $to_vers > ${proj_root}/debian/changelog
fi

#Commit changes to git
if [ "$skip_commit" == "false" ] ; then
    git commit -a -m "New release: $to_vers"
fi

#Create a new tag
if [ "$skip_tag" == "false" ] ; then
    git tag -a v${to_vers} -m "New version: $to_vers"
fi
