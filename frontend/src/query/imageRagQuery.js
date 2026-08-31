import {
    useMutation,
} from "@tanstack/react-query";

import {
    analyzeImage,
} from "../api/imageRagApi";


export const useAnalyzeImage = () => {

    return useMutation({
        mutationFn: analyzeImage,
    });
};