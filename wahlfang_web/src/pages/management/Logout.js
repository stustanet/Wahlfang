import React, {useEffect} from "react";
import Layout from "../../components/Layout";
import {useSetRecoilState} from "recoil";
import {isManagerAuthenticated} from "../../state/management";
import Loading from "../../components/Loading";
import {logoutVoter} from "../../api";


export default function Logout() {
    const setAuthenticated = useSetRecoilState(isManagerAuthenticated);

    useEffect(() => {
        logoutVoter().then(result => {
            setAuthenticated(false);
            // TODO: this is a very hacky way of reloading the whole app such that the recoil app state is reset.
            // TODO: find a saner way of resetting the recoil state without having to force reload the whole page.
            window.location.assign('/');
        });
    })

    return (
        <Layout title="logout">
            <Loading/>
        </Layout>
    );
}
